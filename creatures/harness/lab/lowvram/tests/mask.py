import sys; sys.path.insert(0, 'E:/gen3d'); from mask8 import remove_bg8; from PIL import Image
remove_bg8(Image.open(sys.argv[1])).save(sys.argv[2])
