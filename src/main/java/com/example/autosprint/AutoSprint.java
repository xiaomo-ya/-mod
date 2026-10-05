package com.example.autosprint;

import com.example.autosprint.proxy.CommonProxy;

import cpw.mods.fml.common.Mod;
import cpw.mods.fml.common.SidedProxy;
import cpw.mods.fml.common.event.FMLInitializationEvent;
import cpw.mods.fml.common.event.FMLPreInitializationEvent;

/**
 * 自动疾跑（Auto Sprint）—— Minecraft Forge 1.7.10 客户端 Mod。
 *
 * 功能：只要按住前进键，就自动进入疾跑状态，不需要双击 W，也不用一直按着疾跑键。
 * 游戏内默认按 R 键可以随时开关，配置文件里可以改默认开关和快捷键。
 */
@Mod(
        modid = AutoSprint.MODID,
        name = AutoSprint.NAME,
        version = AutoSprint.VERSION,
        acceptedMinecraftVersions = "[1.7.10]"
)
public class AutoSprint {

    public static final String MODID = "autosprint";
    public static final String NAME = "Auto Sprint";
    public static final String VERSION = "1.0.0";

    @Mod.Instance(AutoSprint.MODID)
    public static AutoSprint instance;

    @SidedProxy(
            clientSide = "com.example.autosprint.proxy.ClientProxy",
            serverSide = "com.example.autosprint.proxy.CommonProxy"
    )
    public static CommonProxy proxy;

    @Mod.EventHandler
    public void preInit(FMLPreInitializationEvent event) {
        ConfigHandler.init(event.getSuggestedConfigurationFile());
        proxy.preInit(event);
    }

    @Mod.EventHandler
    public void init(FMLInitializationEvent event) {
        proxy.init(event);
    }
}
