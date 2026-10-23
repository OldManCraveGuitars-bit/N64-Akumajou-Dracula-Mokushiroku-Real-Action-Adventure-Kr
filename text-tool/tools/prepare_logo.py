"""Decode native title tiles for build verification.

The reviewed Korean logo is bundled as assets/logo/korean-logo-native.png.
"""
from PIL import Image,ImageOps

ENGLISH=(130,76,313,92)

def native_logo(data):
    image=Image.new('RGBA',(320,96))
    for n in range(30):
        pos=0xD608+n*4096
        tile=Image.frombytes('RGBA',(32,32),data[pos:pos+4096])
        image.paste(ImageOps.flip(tile),(n%10*32,n//10*32))
    return image
