"""从 MCP 的 joined.srg + methods.csv/fields.csv 生成三份映射：

  1) obf -> MCP   ：把官方混淆客户端 jar 反混淆成 MCP 名（编译校验用）
  2) MCP -> srg   ：把编译好的 Mod class 重混淆成生产环境需要的 srg 名（func_/field_）
  3) obf -> srg   ：把 Forge universal jar 反混淆（等价于 ForgeGradle 的 forgeBin）

用法: gen_srg.py <mcp_srg.zip> <mcp_stable.zip> <obf2mcp.srg> <mcp2srg.srg> [obf2srg.srg]
"""
import csv
import io
import sys
import zipfile


def load_csv(zip_path, name):
    with zipfile.ZipFile(zip_path) as zf:
        text = zf.read(name).decode('utf-8')
    result = {}
    reader = csv.reader(io.StringIO(text))
    next(reader, None)  # 跳过表头 searge,name,side,desc
    for row in reader:
        if len(row) >= 2 and row[0] and row[1]:
            result[row[0]] = row[1].split(',')[0].strip()
    return result


def main():
    srg_zip, csv_zip, out_obf2mcp, out_mcp2srg = sys.argv[1:5]
    out_obf2srg = sys.argv[5] if len(sys.argv) > 5 else None
    methods = load_csv(csv_zip, 'methods.csv')
    fields = load_csv(csv_zip, 'fields.csv')

    with zipfile.ZipFile(srg_zip) as zf:
        joined = zf.read('joined.srg').decode('utf-8')

    obf2mcp = []
    mcp2srg = []
    obf2srg = []
    classes = []
    n_md = n_fd = 0

    for line in joined.splitlines():
        parts = line.split()
        if not parts:
            continue
        tag = parts[0]

        if tag in ('CL:', 'FD:', 'MD:'):
            obf2srg.append(line)

        if tag == 'CL:':
            obf, srg_class = parts[1], parts[2]
            classes.append(srg_class)
            obf2mcp.append('CL: %s %s' % (obf, srg_class))

        elif tag == 'FD:':
            obf_owner, obf_field = parts[1].rsplit('/', 1)
            srg_owner, srg_field = parts[2].rsplit('/', 1)
            mcp = fields.get(srg_field, srg_field)
            obf2mcp.append('FD: %s/%s %s/%s' % (obf_owner, obf_field, srg_owner, mcp))
            if mcp != srg_field:
                mcp2srg.append('FD: %s/%s %s/%s' % (srg_owner, mcp, srg_owner, srg_field))
            n_fd += 1

        elif tag == 'MD:':
            obf_owner, obf_method = parts[1].rsplit('/', 1)
            obf_desc = parts[2]
            srg_owner, srg_method = parts[3].rsplit('/', 1)
            srg_desc = parts[4]
            mcp = methods.get(srg_method, srg_method)
            obf2mcp.append('MD: %s/%s %s %s/%s %s'
                           % (obf_owner, obf_method, obf_desc, srg_owner, mcp, srg_desc))
            if mcp != srg_method:
                mcp2srg.append('MD: %s/%s %s %s/%s %s'
                               % (srg_owner, mcp, srg_desc, srg_owner, srg_method, srg_desc))
            n_md += 1

    # mcp2srg 里为所有 MC 类补上同名 CL 行，确保 SpecialSource 能建立类映射
    for c in sorted(set(classes)):
        mcp2srg.append('CL: %s %s' % (c, c))

    with open(out_obf2mcp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(obf2mcp) + '\n')
    with open(out_mcp2srg, 'w', encoding='utf-8') as f:
        f.write('\n'.join(mcp2srg) + '\n')
    if out_obf2srg:
        with open(out_obf2srg, 'w', encoding='utf-8') as f:
            f.write('\n'.join(obf2srg) + '\n')

    print('classes=%d methods=%d fields=%d' % (len(classes), n_md, n_fd))
    print('obf2mcp lines=%d -> %s' % (len(obf2mcp), out_obf2mcp))
    print('mcp2srg lines=%d -> %s' % (len(mcp2srg), out_mcp2srg))
    if out_obf2srg:
        print('obf2srg lines=%d -> %s' % (len(obf2srg), out_obf2srg))


if __name__ == '__main__':
    main()
