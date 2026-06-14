#!/usr/bin/env python3
"""批量将 lessons/contrib 中中文文件名改为英文."""
import os, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTRIB = REPO / "lessons" / "contrib"

# 文件名映射: 旧名 → 新名
RENAME = {
    "aily-飞书-mcp-通道-只能拉取不能推送.md": "aily-feishu-mcp-pull-only.md",
    "api-网关不兼容-anthropic-原生格式.md": "api-gateway-anthropic-incompatibility.md",
    "bge-embedding-模型需要降级-fallback-避免启动崩溃.md": "bge-embedding-fallback-crash.md",
    "cc-connect-飞书机器人完整配置指南.md": None,  # already done
    "chroma-建库无-checkpoint-进程一死全部丢失.md": "chroma-rebuild-no-checkpoint-cn.md",
    "chromadb-不能放在-ntfs-文件系统.md": None,  # already has eng version
    "deepseek-tui-agent-模式下-write-file-写入不落地-worktree-git-链接路径断裂.md": None,  # already done
    "fanuc-kl-1086-是代码行号而非错误码.md": None,  # already has eng version
    "fanuc-kl-bytes-ahead-是-karel-内置-procedure.md": None,
    "fanuc-kl-err-abort-vs-err-pause-行为差异.md": "fanuc-kl-err-abort-vs-err-pause.md",
    "fanuc-kl-mm-module-h-kl-禁止-routine-声明.md": "fanuc-kl-mm-module-h-no-routine.md",
    "feishu-wiki批量下载-文件类型处理策略.md": "feishu-wiki-batch-download.md",
    "feishu-凭证轮换后-gateway-必须重启.md": None,  # already has eng version
    "feishu文件上传-file-type-必须用opus.md": "feishu-upload-file-type-opus.md",
    "feishu文档url-必须用api返回值不要拼接.md": "feishu-doc-url-use-api-return.md",
    "ffmpeg音频转码-必须用libopus而非format-ogg.md": "ffmpeg-audio-libopus-not-ogg.md",
    "gateway-进程挂死未崩溃-watchdog-自动恢复.md": "gateway-hang-watchdog-recovery.md",
    "git-凭证和-node-id-node2-加网后必须设置.md": None,  # already done
    "gpt-sovits-hubert-必须16khz且get-model返回单体.md": "gpt-sovits-hubert-16khz.md",
    "gpt-sovits-ref-free-bug-prompt-text为空时参数被覆盖.md": "gpt-sovits-ref-free-bug.md",
    "gpt-sovits训练-2-name2text格式必须用arpabet音素.md": "gpt-sovits-name2text-arpabet.md",
    "hermes-agent-手动更新步骤-update-超时.md": None,  # already done
    "hub-feishuwsclient-start-从未调用-websocket-接收死代码.md": "hub-feishu-wsclient-start-never-called.md",
    "hub-hermes-凭证体系-gateway-vs-hub-各自读哪里.md": "hub-credential-gateway-vs-hub.md",
    "lessons-md-修正-4-处-项目-旧结论-修正后-heading-block-type-4.md": "lessons-md-fix-heading-block-type.md",
    "node2-配置完成-git-credentials-和-node-id-设置.md": None,  # already done
    "openclaw-gateway-动态模块缺失-导致飞书消息分发失败.md": "openclaw-gateway-dynamic-module-missing.md",
    "openclaw-重装教训-删除前先停服务清残留.md": "openclaw-reinstall-lesson.md",
    "rag-cross-encoder-reranker-cpu-瓶颈-与-llm-确定性调优.md": "rag-cross-encoder-cpu-bottleneck.md",
    "rag-三通道-llm-容灾方案.md": "rag-three-channel-llm-disaster-recovery.md",
    "rag-分块参数-800-字符-100-重叠-每文件最多-100-分块.md": "rag-chunk-params-800-100.md",
    "rag-报警代码检索需要关键词强制召回.md": "rag-alarm-code-mandatory-recall.md",
    "rag-检索中文乱码-pymupdf4llm-默认编码问题.md": "rag-chinese-encoding-pymupdf.md",
    "rag建库策略-不可一次性加载全部数据.md": "rag-build-strategy-batch.md",
    "st2-danielstarman-mcp-选rare-relic会卡死.md": None,  # already done
    "st2-mcp-end-turn返回409但游戏正常推进.md": None,  # already done
    "st2-mcp从game-over重开必须走特定流程.md": None,  # already done
    "tts中文编码-powerhsell传参必须用txt文件.md": "tts-chinese-encoding-powershell.md",
    "wcferry-微信版本锁定-3-9-12-51-才能用.md": "wcferry-wechat-version-lock.md",
    "wsl-pip-install-gbk-编码导致-hub-poller-崩溃.md": "wsl-pip-gbk-hub-poller-crash.md",
    "wsl-终端编辑配置危险-tty粘贴吞下划线.md": None,  # already has eng version
    "wsl-需要代理配置才能访问-huggingface-和外部网络.md": "wsl-proxy-huggingface-external.md",
    "wxauto-必须在-windows-python-下安装-不能走-wsl-pip.md": "wxauto-windows-python-not-wsl.md",
    "企业微信机器人-长连接模式不需要-ngrok.md": "wecom-robot-long-connect-no-ngrok.md",
    "知识库-4-质量审计流水线.md": "kb-4sigma-quality-audit-pipeline.md",
    "防火墙端口开放不等于内网穿透.md": "firewall-port-open-not-public.md",
    "飞书-block-api-假成功特征.md": "feishu-block-api-false-success.md",
    "飞书-block-type-正确值与已知限制.md": "feishu-block-type-values-limits.md",
    "飞书-block-批量写入上限.md": "feishu-block-batch-limit.md",
    "飞书-webhook-url-必须用环境变量或-gitignored-的-config-yaml.md": "feishu-webhook-url-env-config.md",
}

def main():
    renamed = 0
    skipped = 0
    not_found = []

    for old, new in sorted(RENAME.items()):
        old_path = CONTRIB / old
        if not old_path.exists():
            not_found.append(old)
            continue
        if new is None:
            # 已有英文版，直接 git rm
            result = subprocess.run(["git", "rm", str(old_path)], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  🗑️  {old} (git rm)")
            else:
                print(f"  ⚠️  git rm failed for {old}: {result.stderr.strip()}")
            continue

        new_path = CONTRIB / new
        # git mv 保留历史
        result = subprocess.run(["git", "mv", str(old_path), str(new_path)], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  🔄 {old} → {new}")
            renamed += 1
        else:
            # fallback: copy + add
            import shutil
            shutil.copy2(old_path, new_path)
            subprocess.run(["git", "add", str(new_path)], capture_output=True)
            print(f"  🔄 {old} → {new} (copy+add, git mv failed: {result.stderr.strip()})")
            renamed += 1

    print(f"\n✅ 重命名: {renamed}, 删除: {sum(1 for v in RENAME.values() if v is None)}, 未找到: {len(not_found)}")
    for f in not_found:
        print(f"  ⚠️  未找到: {f}")

if __name__ == "__main__":
    os.chdir(REPO)
    main()
