package com.example.autosprint.proxy;

import org.lwjgl.input.Keyboard;

import com.example.autosprint.ConfigHandler;
import com.example.autosprint.client.SprintHandler;

import cpw.mods.fml.client.registry.ClientRegistry;
import cpw.mods.fml.common.FMLCommonHandler;
import cpw.mods.fml.common.event.FMLInitializationEvent;
import cpw.mods.fml.common.event.FMLPreInitializationEvent;
import net.minecraft.client.settings.KeyBinding;
import net.minecraftforge.common.MinecraftForge;

/**
 * 客户端代理：注册快捷键和 tick 事件处理器。
 * 所有引用了客户端类（Minecraft / KeyBinding / LWJGL）的代码都必须放在这里，
 * 这样专用服务器加载本 Mod 时不会因为找不到客户端类而崩溃。
 */
public class ClientProxy extends CommonProxy {

    /** 游戏内切换自动疾跑的按键，会出现在「选项 → 控制」里。 */
    public static KeyBinding toggleKey;

    @Override
    public void preInit(FMLPreInitializationEvent event) {
        super.preInit(event);

        int keyCode = ConfigHandler.toggleKeyCode;
        toggleKey = new KeyBinding(
                "key.autosprint.toggle",
                keyCode == 0 ? Keyboard.KEY_NONE : keyCode,
                "key.categories.gameplay");

        ClientRegistry.registerKeyBinding(toggleKey);
    }

    @Override
    public void init(FMLInitializationEvent event) {
        super.init(event);

        SprintHandler handler = new SprintHandler();

        // 1.7.10 的 TickEvent / InputEvent 由 FML 事件总线派发。
        // 这里两个总线都注册一份，纯粹是为了兼容不同 Forge 版本的差异：
        // 同一个事件只会从其中一个总线派发，所以逻辑只会执行一次（处理逻辑本身也是幂等的）。
        FMLCommonHandler.instance().bus().register(handler);
        MinecraftForge.EVENT_BUS.register(handler);
    }
}
