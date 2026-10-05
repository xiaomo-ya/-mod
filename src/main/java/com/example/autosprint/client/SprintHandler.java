package com.example.autosprint.client;

import org.lwjgl.input.Keyboard;

import com.example.autosprint.ConfigHandler;
import com.example.autosprint.proxy.ClientProxy;

import cpw.mods.fml.common.eventhandler.SubscribeEvent;
import cpw.mods.fml.common.gameevent.TickEvent;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityClientPlayerMP;
import net.minecraft.client.settings.GameSettings;
import net.minecraft.client.settings.KeyBinding;
import net.minecraft.util.ChatComponentText;
import net.minecraft.util.EnumChatFormatting;
import net.minecraft.util.StatCollector;

/**
 * 自动疾跑的核心逻辑（纯客户端）。
 *
 * <h3>实现原理</h3>
 * 1.7.10 原版就有「疾跑」这个按键绑定：{@code Minecraft.gameSettings.keyBindSprint}（默认左 Ctrl）。
 * 原版 {@code EntityPlayerSP.onLivingUpdate()} 里会读
 * {@code this.mc.gameSettings.keyBindSprint.getIsKeyPressed()} 来决定要不要疾跑。
 *
 * <p>所以这里不去硬改 {@code player.setSprinting(...)}，而是在每个客户端 tick 结束时调用
 * {@link KeyBinding#setKeyBindState(int, boolean)}，把「疾跑键」假装成一直被按住。这样：
 * <ul>
 *   <li>饱食度 &gt; 6、必须在地面起步、使用物品中、失明效果、撞墙中断、潜行时不能疾跑……
 *       这些原版判定全部原样生效；</li>
 *   <li>疾跑状态与服务器之间的同步由原版完成
 *       （{@code EntityClientPlayerMP.sendMotionUpdates()} 会在状态变化时发送
 *       {@code C0BPacketEntityAction}），我们不需要发任何自定义数据包；</li>
 *   <li>FOV 变化、疾跑粒子、跑步消耗饱食度等表现和原版按住疾跑键完全一致。</li>
 * </ul>
 *
 * <p>也就是说，这个 Mod 的效果 = 自动帮你按住「疾跑键」，不修改任何原版判定，
 * 因此在多人服务器上不会和反作弊产生冲突。
 */
public class SprintHandler {

    private final Minecraft mc = Minecraft.getMinecraft();

    /** 运行时开关。配置文件里的 enabled 只决定启动时的默认值，游戏内可用快捷键随时改。 */
    private boolean autoSprintEnabled = ConfigHandler.enabled;

    @SubscribeEvent
    public void onClientTick(TickEvent.ClientTickEvent event) {
        // 在客户端 tick 结束时处理：此时玩家的 onLivingUpdate() 已经跑完，
        // 我们设置的按键状态会被下一个 tick 的原版逻辑读取。
        if (event.phase != TickEvent.Phase.END) {
            return;
        }

        handleToggleKey();

        if (mc.thePlayer == null || mc.gameSettings == null) {
            return;
        }

        KeyBinding sprintKey = mc.gameSettings.keyBindSprint;
        if (sprintKey == null || sprintKey.getKeyCode() == Keyboard.KEY_NONE) {
            // 玩家把「疾跑」解绑了，没法模拟按键。请在 选项 → 控制 里给疾跑绑定一个按键。
            return;
        }

        // 玩家自己按住疾跑键时保持原样，不去干预
        boolean physicallyHeld = GameSettings.isKeyDown(sprintKey);

        KeyBinding.setKeyBindState(sprintKey.getKeyCode(), physicallyHeld || shouldAutoSprint());
    }

    /** 快捷键：开 / 关自动疾跑，并在聊天栏提示。 */
    private void handleToggleKey() {
        if (ClientProxy.toggleKey == null || !ClientProxy.toggleKey.isPressed()) {
            return;
        }

        autoSprintEnabled = !autoSprintEnabled;

        EntityClientPlayerMP player = mc.thePlayer;
        if (player != null) {
            String langKey = autoSprintEnabled ? "autosprint.msg.enabled" : "autosprint.msg.disabled";
            String color = autoSprintEnabled
                    ? EnumChatFormatting.GREEN.toString()
                    : EnumChatFormatting.RED.toString();

            player.addChatMessage(new ChatComponentText(color + StatCollector.translateToLocal(langKey)));
        }
    }

    /** 是否应该自动按住疾跑键。 */
    private boolean shouldAutoSprint() {
        if (!autoSprintEnabled) {
            return false;
        }

        // 打开 GUI（背包、聊天等）时不要干预
        if (mc.currentScreen != null) {
            return false;
        }

        EntityClientPlayerMP player = mc.thePlayer;
        if (player == null || player.isRiding()) {
            return false;
        }

        // 只看「前进键」是否按住，其余判定全部交给原版
        KeyBinding forwardKey = mc.gameSettings.keyBindForward;
        return forwardKey != null && forwardKey.getIsKeyPressed();
    }
}
