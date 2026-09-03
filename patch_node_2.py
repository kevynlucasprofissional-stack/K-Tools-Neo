import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')
code = code.replace('"format": PortDefinition(DataType.TEXT, required=False),', '')
code = code.replace('out_format = inputs.get("format", config.get("format", "m4a")).lower().strip(".")', 'out_format = config.get("format", "m4a").lower().strip(".")')
p.write_text(code, 'utf-8')
