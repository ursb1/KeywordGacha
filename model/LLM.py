import re
import asyncio
import threading
import urllib.request
from typing import Any
from types import SimpleNamespace

import pykakasi
import json_repair as repair
from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

from base.BaseData import BaseData
from model.NER import NER
from model.Word import Word
from module.Text.TextHelper import TextHelper
from module.LogHelper import LogHelper

class LLM:

    # 任务类型
    class Type(BaseData):

        API_TEST: int = 100                  # 语义分析
        SURFACE_ANALYSIS: int = 200          # 语义分析
        TRANSLATE_CONTEXT: int = 300         # 翻译参考文本

    # 最大重试次数
    MAX_RETRY: int = 3

    # OPENAI 思考模型 o1 o3-mini o4-mini-20240406
    REGEX_O_Series: re.Pattern = re.compile(r"o\d$|o\d\-", flags = re.IGNORECASE)

    # 类型映射表
    GROUP_MAPPING = {
        "角色" : ["姓氏", "名字"],
        "组织" : ["组织", "群体", "家族", "种族"],
        "地点" : ["地点", "建筑", "设施"],
        "物品" : ["物品", "食品", "工具"],
        "生物" : ["生物",],
    }
    GROUP_MAPPING_BANNED = {
        "黑名单" : ["行为", "活动", "其他", "无法判断"],
    }
    GROUP_MAPPING_ADDITIONAL = {
        "角色" : ["角色", "人", "人物", "人名"],
        "组织" : [],
        "地点" : [],
        "物品" : ["食物", "饮品",],
        "生物" : ["植物", "动物", "怪物", "魔物",],
    }

    def __init__(self, config: SimpleNamespace) -> None:
        self.api_key: str = config.api_key
        self.base_url: str = config.base_url
        self.model_name: str = config.model_name
        self.request_timeout: int = config.request_timeout
        self.request_frequency_threshold: int = config.request_frequency_threshold

        # 初始化
        self.kakasi = pykakasi.kakasi()
        self.client = self.load_client()

        # 线程锁
        self.lock = threading.Lock()

    # 初始化 OpenAI 客户端
    def load_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            timeout = self.request_timeout,
            api_key = self.api_key,
            base_url = self.base_url,
            max_retries = 0
        )

    # 设置语言
    def set_language(self, language: int) -> None:
        self.language = language

    # 加载指令
    def load_prompt(self) -> None:
        try:
            with open("prompt/prompt_context_translate.txt", "r", encoding = "utf-8-sig") as reader:
                self.prompt_context_translate = reader.read().strip()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

        try:
            with open("prompt/prompt_surface_analysis_with_translation.txt", "r", encoding = "utf-8-sig") as reader:
                self.prompt_surface_analysis_with_translation = reader.read().strip()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

        try:
            with open("prompt/prompt_surface_analysis_without_translation.txt", "r", encoding = "utf-8-sig") as reader:
                self.prompt_surface_analysis_without_translation = reader.read().strip()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 加载配置文件
    def load_llm_config(self) -> None:
        try:
            with open("resource/llm_config/api_test_config.json", "r", encoding = "utf-8-sig") as reader:
                self.api_test_config = repair.load(reader)
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

        try:
            with open("resource/llm_config/surface_analysis_config.json", "r", encoding = "utf-8-sig") as reader:
                self.surface_analysis_config = repair.load(reader)
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

        try:
            with open("resource/llm_config/context_translate_config.json", "r", encoding = "utf-8-sig") as reader:
                self.context_translate_config = repair.load(reader)
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 设置请求限制器
    def set_request_limiter(self) -> None:
        # 获取 llama.cpp 响应数据
        try:
            response_json = None
            base_url_cleaned = re.sub(r"/v1$", "", self.base_url)
            with urllib.request.urlopen(f"{base_url_cleaned}/slots") as reader:
                response_json = repair.load(reader)
        except Exception:
            LogHelper.debug("无法获取 [green]llama.cpp[/] 响应数据 ...")

        # 如果响应数据有效，则是 llama.cpp 接口
        if isinstance(response_json, list) and len(response_json) > 0:
            self.request_frequency_threshold = len(response_json)
            LogHelper.info("")
            LogHelper.info(f"检查到 [green]llama.cpp[/]，根据其配置，请求频率阈值自动设置为 [green]{len(response_json)}[/] 次/秒 ...")
            LogHelper.info("")

        # 设置请求限制器
        if self.request_frequency_threshold > 1:
            self.semaphore = asyncio.Semaphore(self.request_frequency_threshold)
            self.async_limiter = AsyncLimiter(max_rate = self.request_frequency_threshold, time_period = 1)
        elif self.request_frequency_threshold > 0:
            self.semaphore = asyncio.Semaphore(1)
            self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1 / self.request_frequency_threshold)
        else:
            self.semaphore = asyncio.Semaphore(1)
            self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1)

    # 异步发送请求到 OpenAI 获取模型回复
    async def do_request(self, messages: list, llm_config: dict[str, Any], retry: bool) -> tuple[Exception, dict, str, str, dict, dict]:
        try:
            error, usage, response_think, response_result, llm_request, llm_response = None, None, None, None, None, None

            llm_request = {
                "model" : self.model_name,
                "messages" : messages,
                "max_tokens" : llm_config.get("max_tokens"),
            }

            # 设置请求参数
            if isinstance(llm_config.get("top_p"), (int, float)):
                llm_request["top_p"] = llm_config.get("top_p")
            if isinstance(llm_config.get("temperature"), (int, float)):
                llm_request["temperature"] = llm_config.get("temperature")
            if isinstance(llm_config.get("presence_penalty"), (int, float)):
                llm_request["presence_penalty"] = llm_config.get("presence_penalty")
            if isinstance(llm_config.get("frequency_penalty"), (int, float)):
                llm_request["frequency_penalty"] = llm_config.get("frequency_penalty")
            if isinstance(llm_config.get("extra_headers"), dict):
                llm_request["extra_headers"] = llm_config.get("extra_headers")
            if isinstance(llm_config.get("extra_query"), dict):
                llm_request["extra_query"] = llm_config.get("extra_query")
            if isinstance(llm_config.get("extra_body"), dict):
                llm_request["extra_body"] = llm_config.get("extra_body")

            # 根据是否为 OpenAI O-Series 模型对请求参数进行处理
            if (
                self.base_url.startswith("https://api.openai.com") or
                __class__.REGEX_O_Series.search(self.model_name) is not None
            ):
                llm_request.pop("max_tokens", None)
                llm_request["max_completion_tokens"] = llm_config.get("max_tokens")

            response = await self.client.chat.completions.create(**llm_request)

            # OpenAI 的 API 返回的对象通常是 OpenAIObject 类型
            # 该类有一个内置方法可以将其转换为字典
            llm_response = response.to_dict()

            # 提取回复内容
            usage = response.usage
            message = response.choices[0].message
            if hasattr(message, "reasoning_content") and isinstance(message.reasoning_content, str):
                response_think = message.reasoning_content.replace("\n\n", "\n").strip()
                response_result = message.content.strip()
            elif "</think>" in message.content:
                splited = message.content.split("</think>")
                response_think = splited[0].removeprefix("<think>").replace("\n\n", "\n").strip()
                response_result = splited[-1].strip()
            else:
                response_think = ""
                response_result = message.content.strip()
        except Exception as e:
            error = e
        finally:
            return error, usage, response_think, response_result, llm_request, llm_response

    # 接口测试任务
    async def api_test(self) -> bool:
        async with self.semaphore, self.async_limiter:
            try:
                success = False

                error, usage, _, response_result, llm_request, llm_response = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                self.prompt_surface_analysis_with_translation.replace("{PROMPT_GROUPS}", "、".join(("角色", "其他")))
                                + "\n" + "目标词语：ダリヤ"
                                + "\n" + "参考文本：\n魔導具師ダリヤはうつむかない"
                            ),
                        },
                    ],
                    self.api_test_config,
                    True
                )

                # 检查错误
                if error != None:
                    raise error

                # 反序列化 JSON
                result = repair.loads(response_result)
                if not isinstance(result, dict) or result == {}:
                    raise Exception("返回结果错误（数据结构） ...")

                # 输出结果
                success = True
                LogHelper.info(f"{result}")

                return success
            except Exception as e:
                LogHelper.warning(f"{LogHelper.get_trackback(e)}")
                LogHelper.warning(f"llm_request - {llm_request}")
                LogHelper.warning(f"llm_response - {llm_response}")

    # 词义分析任务
    async def surface_analysis(self, word: Word, words: list[Word], fake_name_mapping: dict[str, str], success: list[Word], retry: bool, last_round: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                if not hasattr(self, "prompt_groups"):
                    x = [v for group in LLM.GROUP_MAPPING.values() for v in group]
                    y = [v for group in LLM.GROUP_MAPPING_BANNED.values() for v in group]
                    self.prompt_groups = x + y

                if self.language != NER.Language.ZH:
                    prompt = self.prompt_surface_analysis_with_translation
                else:
                    prompt = self.prompt_surface_analysis_without_translation

                error, usage, _, response_result, llm_request, llm_response = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                prompt.replace("{PROMPT_GROUPS}", "、".join(self.prompt_groups))
                                + "\n" + f"目标词语：{word.surface}"
                                + "\n" + f"参考文本：\n{word.get_context_str_for_surface_analysis(self.language)}"
                            ),
                        },
                    ],
                    self.surface_analysis_config,
                    retry
                )

                # 检查错误
                if error != None:
                    raise error

                # 反序列化 JSON
                result = repair.loads(response_result)
                if not isinstance(result, dict) or result == {}:
                    raise Exception("返回结果错误（数据结构） ...")

                # 清理一下格式
                for k, v in result.items():
                    result[k] = re.sub(r".*[:：]+", "", TextHelper.strip_punctuation(v))

                # 获取结果
                word.group = result.get("group", "")
                word.gender = result.get("gender", "")
                word.context_summary = result.get("summary", "")
                word.surface_translation = result.get("translation", "")
                word.llmrequest_surface_analysis = llm_request
                word.llmresponse_surface_analysis = llm_response

                # 生成罗马音，汉字有时候会生成重复的罗马音，所以需要去重
                results = list(set([item.get("hepburn", "") for item in self.kakasi.convert(word.surface)]))
                word.surface_romaji = (" ".join(results)).strip()

                # 还原伪名
                fake_name_mapping_ex = {v: k for k, v in fake_name_mapping.items()}
                if word.surface in fake_name_mapping_ex:
                    word.surface = fake_name_mapping_ex.get(word.surface)
                    word.surface_romaji = ""
                    word.surface_translation = ""

                # 匹配实体类型
                matched = False
                for k, v in LLM.GROUP_MAPPING.items():
                    if word.group in set(v):
                        word.group = k
                        matched = True
                        break
                for k, v in LLM.GROUP_MAPPING_ADDITIONAL.items():
                    if word.group in set(v):
                        LogHelper.debug(f"[词义分析] 命中额外类型 - {word.surface} [green]->[/] {word.group} ...")
                        word.group = k
                        matched = True
                        break

                # 处理未命中目标类型的情况
                if matched == False:
                    if last_round == True:
                        LogHelper.warning(f"[词义分析] 无法匹配的实体类型 - {word.surface} [green]->[/] {word.group} ...")
                        word.group = ""
                    else:
                        LogHelper.warning(f"[词义分析] 无法匹配的实体类型 - {word.surface} [green]->[/] {word.group} ...")
                        error = Exception("无法匹配的实体类型 ...")
            except Exception as e:
                LogHelper.warning(f"[词义分析] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error == None:
                    with self.lock:
                        success.append(word)
                    LogHelper.info(f"[词义分析] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行词义分析任务
    async def surface_analysis_batch(self, words: list[Word], fake_name_mapping: dict[str, str]) -> list[Word]:
        failure: list[Word] = []
        success: list[Word] = []

        for i in range(LLM.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[词义分析] 即将开始第 {i} / {LLM.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.surface_analysis(word, words, fake_name_mapping, success, retry, i == LLM.MAX_RETRY))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

            # 获得失败任务的列表
            success_pairs = {(word.surface, word.group) for word in success}
            failure = [word for word in words if (word.surface, word.group) not in success_pairs]

        return words

    # 参考文本翻译任务
    async def context_translate(self, word: Word, words: list[Word], success: list[Word], retry: bool) -> None:
        async with self.semaphore, self.async_limiter:
            try:
                error, usage, _, response_result, llm_request, llm_response = await self.do_request(
                    [
                        {
                            "role": "user",
                            "content": (
                                self.prompt_context_translate
                                + "\n" + f"轻小说文本：\n{word.get_context_str_for_translate(self.language)}"
                            ),
                        },
                    ],
                    self.context_translate_config,
                    retry
                )

                if error != None:
                    raise error

                context_translation = [line.strip() for line in response_result.splitlines() if line.strip() != ""]

                word.context_translation = context_translation
                word.llmrequest_context_translate = llm_request
                word.llmresponse_context_translate = llm_response
            except Exception as e:
                LogHelper.warning(f"[参考文本翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")
                LogHelper.debug(f"llm_request - {llm_request}")
                LogHelper.debug(f"llm_response - {llm_response}")
                error = e
            finally:
                if error == None:
                    with self.lock:
                        success.append(word)
                    LogHelper.info(f"[参考文本翻译] 已完成 {len(success)} / {len(words)} ...")

    # 批量执行参考文本翻译任务
    async def context_translate_batch(self, words: list[Word]) -> list[Word]:
        failure: list[Word] = []
        success: list[Word] = []

        for i in range(LLM.MAX_RETRY + 1):
            if i == 0:
                retry = False
                words_this_round = words
            elif len(failure) > 0:
                retry = True
                words_this_round = failure
                LogHelper.warning(f"[参考文本翻译] 即将开始第 {i} / {LLM.MAX_RETRY} 轮重试...")
            else:
                break

            # 执行异步任务
            tasks = [
                asyncio.create_task(self.context_translate(word, words, success, retry))
                for word in words_this_round
            ]
            await asyncio.gather(*tasks, return_exceptions = True)

            # 获得失败任务的列表
            success_pairs = {(word.surface, word.group) for word in success}
            failure = [word for word in words if (word.surface, word.group) not in success_pairs]

        return words