import matplotlib.font_manager as fm
import pprint

font_list = [f.name for f in fm.fontManager.ttflist]

pprint.pprint(font_list)
