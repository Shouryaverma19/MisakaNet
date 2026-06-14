#!/usr/bin/env python3
"""Update index.md with new English filenames."""
RENAME = {
    'aily-飞书-mcp-通道-只能拉取不能推送.md': 'aily-feishu-mcp-pull-only.md',
    'api-网关不兼容-anthropic-原生格式.md': 'api-gateway-anthropic-incompatibility.md',
    'bge-embedding-模型需要降级-fallback-避免启动崩溃.md': 'bge-embedding-fallback-crash.md',
    'chroma-建库无-checkpoint-进程一死全部丢失.md': 'chroma-rebuild-no-checkpoint-cn.md',
    'fanuc-kl-err-abort-vs-err-pause-行为差异.md': 'fanuc-kl-err-abort-vs-err-pause.md',
    'fanuc-kl-mm-module-h-kl-禁止-routine-声明.md': 'fanuc-kl-mm-module-h-no-routine.md',
    'feishu-wiki批量下载-文件类型处理策略.md': 'feishu-wiki-batch-download.md',
    'feishu文件上传-file-type-必须用opus.md': 'feishu-upload-file-type-opus.md',
    'feishu文档url-必须用api返回值不要拼接.md': 'feishu-doc-url-use-api-return.md',
    'ffmpeg音频转码-必须用libopus而非format-ogg.md': 'ffmpeg-audio-libopus-not-ogg.md',
    'gateway-进程挂死未崩溃-watchdog-自动恢复.md': 'gateway-hang-watchdog-recovery.md',
    'gpt-sovits-hubert-必须16khz且get-model返回单体.md': 'gpt-sovits-hubert-16khz.md',
    'gpt-sovits-ref-free-bug-prompt-text为空时参数被覆盖.md': 'gpt-sovits-ref-free-bug.md',
    'gpt-sovits训练-2-name2text格式必须用arpabet音素.md': 'gpt-sovits-name2text-arpabet.md',
    'hub-feishuwsclient-start-从未调用-websocket-接收死代码.md': 'hub-feishu-wsclient-start-never-called.md',
    'hub-hermes-凭证体系-gateway-vs-hub-各自读哪里.md': 'hub-credential-gateway-vs-hub.md',
    'lessons-md-修正-4-处-项目-旧结论-修正后-heading-block-type-4.md': 'lessons-md-fix-heading-block-type.md',
    'openclaw-gateway-动态模块缺失-导致飞书消息分发失败.md': 'openclaw-gateway-dynamic-module-missing.md',
    'openclaw-重装教训-删除前先停服务清残留.md': 'openclaw-reinstall-lesson.md',
    'rag-cross-encoder-reranker-cpu-瓶颈-与-llm-确定性调优.md': 'rag-cross-encoder-cpu-bottleneck.md',
    'rag-三通道-llm-容灾方案.md': 'rag-three-channel-llm-disaster-recovery.md',
    'rag-分块参数-800-字符-100-重叠-每文件最多-100-分块.md': 'rag-chunk-params-800-100.md',
    'rag-报警代码检索需要关键词强制召回.md': 'rag-alarm-code-mandatory-recall.md',
    'rag-检索中文乱码-pymupdf4llm-默认编码问题.md': 'rag-chinese-encoding-pymupdf.md',
    'rag建库策略-不可一次性加载全部数据.md': 'rag-build-strategy-batch.md',
    'tts中文编码-powerhsell传参必须用txt文件.md': 'tts-chinese-encoding-powershell.md',
    'wcferry-微信版本锁定-3-9-12-51-才能用.md': 'wcferry-wechat-version-lock.md',
    'wsl-pip-install-gbk-编码导致-hub-poller-崩溃.md': 'wsl-pip-gbk-hub-poller-crash.md',
    'wsl-需要代理配置才能访问-huggingface-和外部网络.md': 'wsl-proxy-huggingface-external.md',
    'wxauto-必须在-windows-python-下安装-不能走-wsl-pip.md': 'wxauto-windows-python-not-wsl.md',
    '企业微信机器人-长连接模式不需要-ngrok.md': 'wecom-robot-long-connect-no-ngrok.md',
    '知识库-4-质量审计流水线.md': 'kb-4sigma-quality-audit-pipeline.md',
    '防火墙端口开放不等于内网穿透.md': 'firewall-port-open-not-public.md',
    '飞书-block-api-假成功特征.md': 'feishu-block-api-false-success.md',
    '飞书-block-type-正确值与已知限制.md': 'feishu-block-type-values-limits.md',
    '飞书-block-批量写入上限.md': 'feishu-block-batch-limit.md',
    '飞书-webhook-url-必须用环境变量或-gitignored-的-config-yaml.md': 'feishu-webhook-url-env-config.md',
}

with open('/mnt/c/Users/hp/MisakaNet/lessons/index.md', encoding='utf-8') as f:
    content = f.read()

for old, new in RENAME.items():
    content = content.replace(old, new)

with open('/mnt/c/Users/hp/MisakaNet/lessons/index.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('index.md updated')
