"""手工构建流水线的辅助脚本（等价于 ForgeGradle 的 merge / reobf / 打包）。

  merge : 把反混淆后的 MC 全部 class 与编译好的 Mod class 合并成 merge.jar
          （SpecialSource 需要 MC 的类层次结构才能正确重映射继承来的方法）
  pack  : 从重映射结果里取出 com/example/** 的 class，加上 mcmod.info / lang，打成最终 jar
"""
import os
import sys
import zipfile

MOD_PACKAGE = 'com/example/autosprint/'
VERSION = '1.0.0'
MC_VERSION = '1.7.10'


def merge(build):
    tools = os.path.join(build, 'tools')
    classes_mcp = os.path.join(build, 'classes-mcp')
    merge_jar = os.path.join(build, 'merge.jar')
    count = 0
    with zipfile.ZipFile(os.path.join(tools, 'mc-mcp.jar')) as zin, \
            zipfile.ZipFile(merge_jar, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.upper().startswith('META-INF/'):
                continue
            zout.writestr(item, zin.read(item.filename))
            count += 1
        for root, _dirs, files in os.walk(classes_mcp):
            for name in files:
                if not name.endswith('.class'):
                    continue
                full = os.path.join(root, name)
                arc = os.path.relpath(full, classes_mcp).replace('\\', '/')
                zout.write(full, arc)
                count += 1
    print('merge: %d entries -> %s' % (count, merge_jar))


def pack(build, proj, out_jar):
    src_jar = os.path.join(build, 'merge-srg.jar')
    resources = os.path.join(proj, 'src', 'main', 'resources')
    manifest = ('Manifest-Version: 1.0\r\n'
                'Created-By: AutoSprint manual build\r\n'
                '\r\n')
    mod_count = 0
    with zipfile.ZipFile(src_jar) as zin, \
            zipfile.ZipFile(out_jar, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr('META-INF/MANIFEST.MF', manifest)
        for item in zin.infolist():
            if item.filename.startswith(MOD_PACKAGE) and item.filename.endswith('.class'):
                zout.writestr(item, zin.read(item.filename))
                mod_count += 1

        # mcmod.info：替换 ${version} / ${mcversion}（与 ForgeGradle processResources 的 expand 等价）
        info_path = os.path.join(resources, 'mcmod.info')
        with open(info_path, 'r', encoding='utf-8') as f:
            info = f.read()
        info = info.replace('${version}', VERSION).replace('${mcversion}', MC_VERSION)
        zout.writestr('mcmod.info', info.encode('utf-8'))

        # assets/**.lang 原样拷贝（保持 UTF-8）
        assets_dir = os.path.join(resources, 'assets')
        for root, _dirs, files in os.walk(assets_dir):
            for name in files:
                full = os.path.join(root, name)
                arc = os.path.relpath(full, resources).replace('\\', '/')
                with open(full, 'rb') as f:
                    zout.writestr(arc, f.read())

    print('pack: %d mod classes -> %s' % (mod_count, out_jar))
    with zipfile.ZipFile(out_jar) as zf:
        for n in zf.namelist():
            print('   ', n)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'merge':
        merge(sys.argv[2])
    elif mode == 'pack':
        pack(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit('unknown mode: ' + mode)
