# Auto Sprint —— Minecraft Forge 1.7.10 自动疾跑 Mod

按住前进键（默认 `W`）就自动进入疾跑状态：**不用双击 W，也不用一直按着疾跑键**。
纯客户端 Mod，单机 / 多人服务器都能用，不修改任何原版判定。

| 项目 | 值 |
| --- | --- |
| Mod ID | `autosprint` |
| 支持版本 | Minecraft 1.7.10 (Forge 10.13.4.1614) |
| 运行端 | 仅客户端（装在服务端上也不会崩，只是没作用） |
| 开关快捷键 | 默认 `R`（可在「选项 → 控制」里改） |
| 配置文件 | `.minecraft/config/autosprint.cfg` |
| 产物 | `build/libs/AutoSprint-1.7.10-1.0.0.jar`（**已构建好，可直接使用**） |

> ✅ 现成 jar：[AutoSprint-1.7.10-1.0.0.jar](build/libs/AutoSprint-1.7.10-1.0.0.jar)
> —— 6.6 KB，SHA1 `0b4fadeb20d87d35bd68de527e3bdc339563f9c3`（作者：小末）。
> 已用**真实的 1.7.10 反混淆 API 编译通过**，并重混淆为生产环境要求的 srg 名（`func_*` / `field_*`）。
> 想自己重新构建见 [第 3 节](#3-编译)。

---

## 1. 功能

- 按住前进键自动疾跑，松开即停。
- 保留原版全部疾跑规则（见下文「实现原理」）：
  饱食度 ≤ 6、使用物品（吃食物 / 拉弓）、失明效果、撞墙、潜行时都不会强行疾跑。
- 游戏内按 `R` 随时开 / 关，聊天栏会给出提示。
- 疾跑判定与联网同步全部交给原版，**不发送任何自定义数据包**，不会触发反作弊。

> 想改包名 / Mod 名 / 作者？改 `com.example.autosprint`、`Auto Sprint` 即可；作者在
> `src/main/resources/mcmod.info` 的 `authorList` 里（当前为 `小末`，中文要写成 `\uXXXX` 转义，
> 原因见 [第 7 节](#7-常见问题) 的乱码条目）。

---

## 2. 目录结构

```
AutoSprint-1.7.10/
├── build.gradle                     # ForgeGradle 1.2 构建脚本（备选方案）
├── settings.gradle
├── gradle.properties                # 反编译需要 3G 内存 + HTTP 超时
├── README.md
├── build/libs/
│   └── AutoSprint-1.7.10-1.0.0.jar  # ★ 已构建好的成品 jar，直接丢进 .minecraft/mods
├── tools/                           # 不依赖 ForgeGradle 的构建链（推荐，见第 3 节）
│   ├── build-manual.ps1             #   powershell -File tools\build-manual.ps1
│   ├── gen_srg.py                   #   MCP 映射合成
│   └── pack.py                      #   合并 / 重混淆辅助 / 打包
└── src/main/
    ├── java/com/example/autosprint/
    │   ├── AutoSprint.java          # @Mod 主类，读配置 + 调用代理
    │   ├── ConfigHandler.java       # config/autosprint.cfg
    │   ├── proxy/
    │   │   ├── CommonProxy.java     # 服务端：空实现
    │   │   └── ClientProxy.java     # 客户端：注册快捷键 + tick 处理器
    │   └── client/
    │       └── SprintHandler.java   # ★ 自动疾跑核心逻辑
    └── resources/
        ├── mcmod.info
        └── assets/autosprint/lang/{en_US,zh_CN}.lang
```

---

## 3. 编译

### 3.1 推荐：`tools/build-manual.ps1`（不依赖 ForgeGradle）

这是**当前唯一稳定可用**的方式（原因见 3.3）。

```powershell
powershell -ExecutionPolicy Bypass -File tools\build-manual.ps1
```

| 需要 | 说明 |
| --- | --- |
| JDK 8 | 没设 `JAVA_HOME` 时用 `-JavaHome 'C:\Program Files\Java\jdk-1.8'` 指定 |
| Python 3 | PATH 里没有就用 `-Python 'C:\path\to\python.exe'` 指定 |
| 网络 | 首次约 12 MB 下载（官方客户端 jar、MCP 映射、Forge、SpecialSource、LWJGL），已下载过会跳过 |

它做的事，每一步都等价于 ForgeGradle 内部的同名任务：

1. `tools/gen_srg.py` 用 MCP 的 `joined.srg` + `methods.csv` / `fields.csv` 合成三份映射（obf→MCP、MCP→srg、obf→srg）；
2. SpecialSource 把官方混淆客户端 jar 反混淆成 MCP 名 → 编译用 classpath；
3. SpecialSource 把 Forge universal jar 反混淆成 srg 名（等价于 ForgeGradle 的 forgeBin）；
4. `javac -encoding UTF-8 -source 1.7 -target 1.7` 编译 `src/main/java`；
5. `tools/pack.py` 把 Mod 的 class 与 MC 的 class 合并（SpecialSource 需要 MC 的类层次结构才能重映射继承成员，例如 `Entity.isRiding()`），用 MCP→srg 映射重混淆，再只取出 Mod 的 class 打成 jar。

产物：`build/libs/AutoSprint-1.7.10-1.0.0.jar`，中间文件都在 `build-manual/`（可随时删除）。

### 3.2 备选：ForgeGradle（需先处理 3.3 的问题）

| 工具 | 版本要求 | 说明 |
| --- | --- | --- |
| JDK | **8**（必须 8，不要用 11 / 17 / 21） | ForgeGradle 1.2 在 Java 8 上才能正常工作 |
| Gradle | **2.14.x**（不要用 4.x / 5.x / 7.x） | 新版 Gradle 与 ForgeGradle 1.2 不兼容 |

```bash
gradle setupDecompWorkspace    # 首次执行，下载 + 反编译 MC，10~30 分钟，请耐心等待
gradle build                   # 编译打包
```

### 3.3 已知问题：ForgeGradle 1.2 的下载地址已失效

ForgeGradle 1.2 硬编码从 `http://s3.amazonaws.com/Minecraft.Download/...` 下载客户端 / 服务端 jar
和版本 json，这个地址**现在已经 404**，因此 `gradle setupDecompWorkspace` 会卡住或直接报错。
两种处理方式：

- **预置缓存**（让它不用下载）：把官方 jar 放到 ForgeGradle 期望的位置
  - `~/.gradle/caches/minecraft/net/minecraft/minecraft/1.7.10/minecraft-1.7.10.jar`
  - `~/.gradle/caches/minecraft/net/minecraft/minecraft_server/1.7.10/minecraft_server-1.7.10.jar`

  版本 json（编译时要靠它拿到 lwjgl 等库）可从 `https://bmclapi2.bangbang93.com/version/1.7.10/json` 获取；
  必要时用 [tools/patch-forgegradle-urls.py](tools/patch-forgegradle-urls.py) 把插件 jar 里那几个 S3 URL 改写到镜像
  （用法见文件头注释；本仓库构建时就是这么做的）。
- 或者直接用 3.1 的脚本，完全绕开 ForgeGradle。

### 3.4 在 IDE 里开发 / 调试

```bash
gradle setupDecompWorkspace idea     # Intelij IDEA
gradle setupDecompWorkspace eclipse  # Eclipse
```

以 Gradle 项目导入工程后，ForgeGradle 1.2 会生成 `GradleStart` 启动类，直接运行它即可带 Mod 启动游戏。
单机测试时把 Mod 放进 `run/mods/`（或直接用生成的启动类 + 官方启动器）。

### 3.5 只想把源码拷进现有工程？

把 `src/main/java` 下的 5 个 `.java` 文件（`AutoSprint` / `ConfigHandler` / `CommonProxy` / `ClientProxy` / `SprintHandler`）拷进你已有的 1.7.10 工程，
再把 `src/main/resources` 里的 `mcmod.info` 和 `lang` 文件拷过去即可，代码不依赖任何第三方库。

---

## 4. 安装（给玩家）

1. 安装对应 1.7.10 的 Forge（10.13.4.1614 或更高）。
2. 把 `AutoSprint-1.7.10-1.0.0.jar` 放进 `.minecraft/mods/`。
3. 启动游戏，进游戏后按住 `W` 就会自动疾跑；按 `R` 可开关。

---

## 5. 配置

首次启动会生成 `config/autosprint.cfg`（名字取决于 modid，一般就是 `autosprint.cfg`）：

```ini
general {
    # 是否默认开启自动疾跑（游戏内可用快捷键切换）。
    B:enabled=true

    # 游戏内切换自动疾跑的按键键码（LWJGL key code）。19 = R，0 = 关闭该快捷键。
    I:toggleKeyCode=19
}
```

常用 LWJGL 键码：`R=19`、`G=34`、`B=48`、`V=47`、`N=49`、`右 Shift=54`、`小键盘 0=82`、`0=禁用`。

另外，「选项 → 控制」里会出现一条 **切换自动疾跑 / Toggle Auto Sprint**，也可以在那里改键（改的是当前游戏的按键绑定，
和配置文件是两套；改配置文件影响的是默认键位）。

> 注意：请保证「疾跑」这个原版按键处于绑定状态（默认左 `Ctrl`）。如果玩家把它设成「未绑定」，
> 本 Mod 无法模拟按键，会自动跳过（这是有意为之，避免误触其它未绑定按键）。

---

## 6. 实现原理

1.7.10 原版本身就有独立的「疾跑键」（`GameSettings.keyBindSprint`，默认左 Ctrl），
原版 `EntityPlayerSP.onLivingUpdate()` 中会读取：

```java
if (!this.isSprinting() && this.movementInput.moveForward >= 0.8F && var4 /* 饱食度 > 6 或允许飞行 */
        && !this.isUsingItem() && !this.isPotionActive(Potion.blindness)
        && this.mc.gameSettings.keyBindSprint.getIsKeyPressed()) {
    this.setSprinting(true);
}
if (this.isSprinting() && (this.movementInput.moveForward < 0.8F || this.isCollidedHorizontally || !var4)) {
    this.setSprinting(false);
}
```

所以本 Mod 的做法是：在客户端 tick 结束时（`TickEvent.ClientTickEvent`，`Phase.END`）调用

```java
KeyBinding.setKeyBindState(mc.gameSettings.keyBindSprint.getKeyCode(), 按住前进键);
```

也就是**帮玩家一直按住「疾跑键」**，而不是硬改 `player.setSprinting(...)`。好处：

- 疾跑的全部前置条件与中断条件仍由原版判断，行为 100% 符合原版规则（不会出现「饿着肚子还能疾跑」「边吃东西边疾跑」这类越权行为）；
- 疾跑状态与服务器的同步由原版完成：`EntityClientPlayerMP.sendMotionUpdates()` 检测到疾跑状态变化时会发送
  `C0BPacketEntityAction(4/5)`，我们不需要自己发包；
- FOV 拉伸、疾跑粒子、饱食度消耗等表现与原版完全一致；
- 玩家自己按住疾跑键时（`GameSettings.isKeyDown`）逻辑直接放行，不产生干扰。

唯一的取舍：原版撞到方块会中断疾跑，这是原版设定，本 Mod 保留（想改成「贴墙也保持疾跑」需要 ASM/Coremod 改写
`EntityPlayerSP`，不在本工程范围内）。

---

## 7. 常见问题

| 现象 | 原因 / 解决 |
| --- | --- |
| `gradle build` 报 `Unsupported class file major version` 之类 | JDK 版本不是 8，换 JDK 8 再试 |
| `setupDecompWorkspace` 卡住 / OOM | 确认 `gradle.properties` 里 `org.gradle.jvmargs=-Xmx3G`，并在带网络的机器上执行 |
| 下载依赖失败 | 换网络 / 挂代理；`build.gradle` 里的 `https://maven.minecraftforge.net/` 可换成你自己的镜像 |
| `setupDecompWorkspace` 卡住或 404 | ForgeGradle 1.2 的 MC 下载地址（S3）已停服，见 [3.3](#33-已知问题forgegradle-12-的下载地址已失效)；或直接用 `tools/build-manual.ps1` |
| Mod 列表里中文描述乱码 | 1.7.10 的 FML 用**平台默认编码**（中文 Windows 是 GBK）读 `mcmod.info`，所以这个文件必须只含 ASCII，中文写成 `\uXXXX` 转义（`assets/**/*.lang` 不受影响，它按 UTF-8 读取） |
| 游戏里按键无效 | 先看「选项 → 控制」里「疾跑」是否被解绑；再看 `config/autosprint.cfg` 的 `enabled` 与 `toggleKeyCode` |
| 撞墙就停 / 吃饱度不够不跑 | 原版设定，属于预期行为（见「实现原理」） |
| 和别的改疾跑逻辑的 Mod 冲突 | 把那个 Mod 的疾跑功能关掉其一即可；本 Mod 只操作原版按键状态 |

---

## 8. 说明

- 代码里没有自定义网络包、没有 ASM、没有 Mixin，只用了 1.7.10 稳定的 Forge API 与 LWJGL，
  因此在不同版本的 Forge 1.7.10 上兼容性都很好。
- `.lang` 文件是 UTF-8 编码，请不要用 GBK 另存，否则中文会乱码。
