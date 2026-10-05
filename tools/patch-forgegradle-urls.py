"""把 ForgeGradle 插件 jar 里已停服的下载地址改写到可用镜像（仅在用 ForgeGradle 构建时才需要）。

背景：ForgeGradle 1.2 硬编码从 http://s3.amazonaws.com/Minecraft.Download/... 下载
客户端 / 服务端 jar、版本 json 和资源索引，这些地址现在都已 404。

做法：直接改写 class 文件常量池里的 UTF8 常量。常量池是顺序结构、没有任何指向文件
绝对偏移的引用，所以改变某个常量的长度是安全的。

用法:
    python patch-forgegradle-urls.py <原始 ForgeGradle.jar> <输出.jar> [资源索引 URL]

资源索引 URL 可以从版本 json 里取，例如：
    https://launchermeta.mojang.com/v1/packages/<sha1>/1.7.10.json
（1.7.10 的版本 json： https://bmclapi2.bangbang93.com/version/1.7.10/json 里的 assetIndex.url）
"""
import struct
import sys
import zipfile

DEFAULT_ASSET_INDEX = 'https://launchermeta.mojang.com/v1/packages/1863782e33ce7b584fc45b037325a1964e095d3e/1.7.10.json'

EXACT = {
    # MC 客户端 jar
    'http://s3.amazonaws.com/Minecraft.Download/versions/{MC_VERSION}/{MC_VERSION}.jar':
        'https://bmclapi2.bangbang93.com/version/{MC_VERSION}/client',
    # MC 服务端 jar
    'http://s3.amazonaws.com/Minecraft.Download/versions/{MC_VERSION}/minecraft_server.{MC_VERSION}.jar':
        'https://bmclapi2.bangbang93.com/version/{MC_VERSION}/server',
    # 版本 json（里面是 libraries 列表，编译时要用到 lwjgl 等）
    'http://s3.amazonaws.com/Minecraft.Download/versions/{MC_VERSION}/{MC_VERSION}.json':
        'https://bmclapi2.bangbang93.com/version/{MC_VERSION}/json',
    # 资源索引（内容随版本变化，由命令行参数给出）
    'https://s3.amazonaws.com/Minecraft.Download/indexes/{ASSET_INDEX}.json': None,
    'http://files.minecraftforge.net/fernflower-fix-1.0.zip':
        'https://files.minecraftforge.net/fernflower-fix-1.0.zip',
    'http://resources.download.minecraft.net':
        'https://resources.download.minecraft.net',
}

PREFIX = [
    # 老地址会走一次重定向，直接换成新域名
    ('http://files.minecraftforge.net/maven', 'https://maven.minecraftforge.net'),
]


def make_transform(asset_index_url):
    def transform(s):
        if s in EXACT:
            repl = EXACT[s]
            return asset_index_url if repl is None else repl
        for old, new in PREFIX:
            if s.startswith(old):
                return new + s[len(old):]
        return s
    return transform


def patch_class(data, transform):
    if data[:4] != b'\xca\xfe\xba\xbe':
        return data, 0
    out = bytearray(data)
    count = struct.unpack_from('>H', out, 8)[0]
    pos = 10
    i = 1
    changed = 0
    while i < count:
        tag = out[pos]
        if tag == 1:  # CONSTANT_Utf8
            ln = struct.unpack_from('>H', out, pos + 1)[0]
            raw = bytes(out[pos + 3:pos + 3 + ln])
            try:
                s = raw.decode('utf-8')
            except UnicodeDecodeError:
                s = None
            if s is not None:
                ns = transform(s)
                if ns != s:
                    nb = ns.encode('utf-8')
                    out[pos + 1:pos + 3] = struct.pack('>H', len(nb))
                    out[pos + 3:pos + 3 + ln] = nb
                    pos += 3 + len(nb)
                    i += 1
                    changed += 1
                    continue
            pos += 3 + ln
        elif tag in (7, 8, 16, 19, 20):
            pos += 3
        elif tag == 15:
            pos += 4
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag in (5, 6):
            pos += 9
            i += 1
        else:
            raise ValueError('unknown constant pool tag %d at %d' % (tag, pos))
        i += 1
    return bytes(out), changed


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    asset_index = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_ASSET_INDEX
    transform = make_transform(asset_index)
    total = 0
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith('.class'):
                data, changed = patch_class(data, transform)
                total += changed
            name_upper = item.filename.upper()
            if name_upper.startswith('META-INF/') and name_upper.endswith(('.SF', '.RSA', '.DSA')):
                continue  # 改写后签名必然失效，直接丢弃签名文件
            zout.writestr(item, data)
    print('patched %d constant(s) -> %s' % (total, dst))


if __name__ == '__main__':
    main()
