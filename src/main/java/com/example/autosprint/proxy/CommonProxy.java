package com.example.autosprint.proxy;

import cpw.mods.fml.common.event.FMLInitializationEvent;
import cpw.mods.fml.common.event.FMLPreInitializationEvent;

/**
 * 服务端 / 通用代理：什么也不做。
 * 这个 Mod 是纯客户端 Mod，装在服务端上不会有任何影响，也不会崩溃。
 */
public class CommonProxy {

    public void preInit(FMLPreInitializationEvent event) {
        // 无需注册任何东西
    }

    public void init(FMLInitializationEvent event) {
        // 无需注册任何东西
    }
}
