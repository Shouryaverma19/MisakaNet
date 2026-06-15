PR 评估:OPENCLAW_ERROR_HANDLER 环境变量钩子
✅ 设计上 OK 的部分(原文说对了的)
context.reason 字段确实存在 ✅dist/index.js:54 / 67 实际就是 runFatalErrorHooks({ reason: "uncaught_exception", error }) 和 runFatalErrorHooks({ reason: "legacy_cli_failure", error })。hook 签名确实是 (context) => string | void,作者读懂了 dist。
现有 registerFatalErrorHook API 确实存在 ✅dist/diagnostic-stability-bundle 已经用它做"崩溃时写 stability bundle",说明这个 hook 点是有意暴露给内部模块的(不是 private)。
OPENCLAW_GATEWAY_STARTUP_TRACE 这个对照锚点真实存在 ✅docs/cli/gateway.md:132 确认了"通过环境变量切粒度"是有先例的模式。
非阻塞 + detached + unref() 的"零影响"声明基本成立 ✅这部分代码逻辑上确实不会延迟 OpenClaw 退出。
🚨 严重问题(需要原 PR 里看到之前我必须指出的)
1. 安全性:shell: true + 用户/操作员可设环境变量 = 命令注入面(致命)
spawn(handler, [], { ..., shell: true })
shell: true 配合一个完整命令字符串 = 完整 shell 解析。
任何人只要能控制 OpenClaw 进程的环境变量(被嵌入 OpenClaw 的子进程、容器 init 系统、被恶意 webhook/payload 改 env 的场景)就能执行任意命令。
原文写"/usr/bin/nonexistent_file 优雅降级"——这等于在演示"我们相信 environment 来源",但环境变量来源在 OpenClaw 多 agent / node 拓扑里并不一定干净:
节点命令参数可注入(看过 docs/nodes/)
飞书 / 邮件 / webhook 进来的 payload 在某些路径下会写进子进程 env
多 agent 共享环境(MEMORY.md 里克莱恩拍过板:多 agent 共享账号的规则)
最起码要求:文档明写"仅信任来自受控 systemd / docker-compose env 的值;不要让任何半信任输入写入此变量";或干脆 shell: false + 强校验"必须是单一可执行文件路径,不允许空格/引号"。
退一步:spawn 第一参数传数组 ["/usr/bin/handler", "--mode=error"] 风格,不做 shell 解析。
2. process.exit 不会等 stdin flush(隐性 bug)
child.stdin.write(payload);
child.stdin.end();
child.unref();
stdio: ["pipe", "inherit", "inherit"] 下,子进程是 detached 的,unref() 后父进程不等子进程。
父进程跑完 runExternalErrorHandler 紧接着 process.exit(1)(dist/index.js:60)。
真实场景:handler 还没读完 payload,父进程就死了。pipe 写一半被截断的概率 = 100%,取决于 handler 启动速度。
正确做法(在 handler 启动比父进程退出慢的所有情形):process.on('exit', ...) 同步等待 / 或者用 stdio: 'inherit' + 传 argv(让父进程不退出直到 handler 收到 EOF)。
作者用 cat 测试看不出来问题,因为 cat 本来就立刻把 stdin 读完了。换成 jq .timestamp / 网络 webhook 就立刻翻车。
3. context 只取 reason,丢掉 error(信息损失,作者可能误读了 dist)
dist 里 context.error 是 Error 对象,带 .stack、.name、可能的 .code、isOpenClawError 标志。原文只传 reason + timestamp + pid —— 报错现场的关键 stack / 错误链全丢了。
验证 demo cat 输出是看不出这点的(cat 给你的是 payload 本身)。
这会让所谓"高级 observability / 报警"价值大幅缩水。建议至少:
4. payload 不带 schemaVersion(前向兼容隐患)
Opire / microG / Discord 这些对方收到 JSON 怎么知道字段集?现在 3 个字段还能改,以后加字段会破坏现有 handler。建议加 schemaVersion: 1。
5. 失败被 try...catch 完全吞掉(作者主动写"silently degraded",但应该至少打 warning)
"silently degraded" 在生产里 = 排查地狱。OpenClaw 自己挂了 + handler 也没启动 = 没人知道。
建议:catch 里 console.error 一次(失败但没 crash exit);或者提供一个 OPENCLAW_ERROR_HANDLER_DEBUG=1 模式。
6. 不区分 reason 类型(对下游消费方不友好)
context.reason 当前已知值:"uncaught_exception" / "legacy_cli_failure"。handler 收到 "subagent 异常" vs "启动期 unhandled rejection" 行为应该不同。至少应该把 reason 完整透传 + 包含 exit code / argv 摘要,让下游决策。
7. import { spawn } from "node:child_process" 重复声明(如果文件已经有)
未读源文件不能 100% 确认 —— 但要提醒作者合并现有 import,避免 PR review 时被 nit-pick。
⚖️ 整体评级
维度
评分
评语
功能/动机
🟢 合理
OpenClaw 当前崩溃时确实没有"操作员自定义 hook"的标准机制,这个口子有真实需求
跟现有架构契合度
🟢 高
跟 registerFatalErrorHook 是天然正交扩展(没动内部 hook 集合),跟 OPENCLAW_GATEWAY_STARTUP_TRACE 是同一思路
实现正确性
🔴 有阻塞 bug
stdin flush 时序问题 + 丢 error 字段
安全性
🔴 有阻塞问题
shell: true + 不可信 env 来源 = 命令注入面
文档 / 用户面
🟡 待补
应明写 env 来源信任假设 + payload schema + 已知 reason 值
复杂度
🟢 极低
27 行,依赖零
结论:方向对,但现在合会带两个会让维护者皱眉的问题(安全 + flush 时序)。我建议:
怎么改才值得提
去掉 shell: true —— spawn(handlerPath, { stdio: ["pipe", "inherit", "inherit"], detached: true, unref }),handler 必须是单一可执行文件路径。
加 process.on('exit') 同步等待 flush —— 用 child.stdin.write 之后 child.stdin.end(),然后在 'exit' handler 里 child.stdin.destroy() 之前用 sync fsync(但 pipe 不能 fsync...),更现实做法是别 unref 或把 handler 进程 inline 同步跑到一个 boundary;或者直接 stdio: 'inherit' + 把 payload 当作 argv 的一部分传(丢掉 stdin 依赖,绕开时序问题)。最干净的修法:handler 命令本身接收 argv,如 OPENCLAW_ERROR_HANDLER="/usr/local/bin/oc-error-handler",payload 拆字段:然后 handler 自己去读 stack(从 argv / 从 core dump / 从 OpenClaw 的 stability bundle 路径)。
加 schemaVersion: 1,以及 name/stack 字段(注意 token 脱敏)。
catch 改 console.error,别 silently。
README 一段写明:
信任假设(env 来源)
payload schema 草案
已知 reason 值
与现有 registerFatalErrorHook(internal API)的区别