package com.example.autosprint;

import java.io.File;

import net.minecraftforge.common.config.Configuration;

/**
 * 配置文件（config/autosprint.cfg）。
 * 这里的值只在游戏启动时读取一次；游戏内用快捷键切换的开关不会写回文件。
 */
public class ConfigHandler {

    public static final String CATEGORY = "general";

    /** 启动时是否默认开启自动疾跑。 */
    public static boolean enabled = true;

    /**
     * 游戏内切换自动疾跑的按键（LWJGL 键码，19 = R 键，0 = 不要这个快捷键）。
     * 常用键码：R=19，G=34，B=48，V=47，N=49，右 Shift=54，小键盘 0=82。
     */
    public static int toggleKeyCode = 19;

    public static void init(File configFile) {
        Configuration config = new Configuration(configFile);

        try {
            config.load();

            enabled = config.getBoolean(
                    "enabled", CATEGORY, enabled,
                    "是否默认开启自动疾跑（游戏内可用快捷键切换）。\n"
                            + "Enable auto sprint by default. You can still toggle it in game with the hotkey.");

            toggleKeyCode = config.getInt(
                    "toggleKeyCode", CATEGORY, toggleKeyCode, 0, 255,
                    "游戏内切换自动疾跑的按键键码（LWJGL key code）。19 = R，0 = 关闭该快捷键。\n"
                            + "LWJGL key code of the toggle hotkey. 19 = R, 0 = disabled.");
        } catch (Exception e) {
            System.err.println("[AutoSprint] 读取配置文件失败 / Failed to load config: " + e);
            e.printStackTrace();
        } finally {
            if (config.hasChanged()) {
                config.save();
            }
        }
    }
}
