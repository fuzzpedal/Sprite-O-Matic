#!/usr/bin/python

import getopt
import glob
import os
import re
import sys

from PIL import Image


IMAGE_TYPES = ['gif',
               'jpg',
               'jpeg',
               'png']

HTML_TPL = \
"""
<html>
  <head>
    <link rel="stylesheet" type="text/css" href="%(css_file)s"></link>
    <style>
      body { background: #ccc; }
      div { margin: 2px; }
    </style>
  </head>
  <body>
%(body)s
  </body>
</html>
"""

CSS_TPL = \
""".%(class_name)s {
  width: %(w)s;
  height: %(h)s;
  background-position: %(x)s %(y)s;
}
"""

class SpriteOMatic(object):
    """ Creates one image from all images in a specified directory
        Generates css file with background-position (file name is used as class name)
        and an html file for testing
    """
    def __init__(self, img_dir, sprite_dir=None, css_dir=None, alpha=1, debug=False):
        self.curdir = os.path.abspath(os.path.curdir)
        
        self.img_dir = img_dir
        self.sprite_dir = sprite_dir or self.curdir
        self.css_dir = css_dir or self.curdir
        self.alpha = alpha
        self.debug=debug
        
        if not sprite_dir:
            sprite_dir = self.curdir
        if not css_dir:
            css_dir = self.curdir
        
        self.sprite_path = os.path.join(self.sprite_dir, "sprites.png")
        
        
    def run(self):
        images = self.get_images(self.img_dir)
        img_positions = self.stitch_images(images)
        self.create_css(img_positions)
        class_names = [image.get('name') for image in images]
        self.create_html(class_names)
            
    def filename_to_classname(self, filename):
        filename = '-'.join(filename.split('.')[:-1]).split("/")[-1].lower()
        return re.sub('[_ ]', '-', filename)
    
    def get_images(self, path):
        if os.path.isdir(path):
            images = []
            for img_type in IMAGE_TYPES:
                for img in glob.glob( os.path.join(path, '*.%s' % img_type) ):
                    images.append({'name': self.filename_to_classname(img),
                                   'image': Image.open(img),
                                   })
            
            return images
            
        else:
            raise IOError("%s is not a valid directory" % path)
            
    def stitch_images(self, images):
        x_pos = 0
        y_pos = 0
        w = 0
        h = 0
        
        img_positions = {}
        
        for image in images:
            im = image.get('image')
            w += im.size[0]
            if h < im.size[1]:
                h = im.size[1]
        
        if self.alpha:
            sprite = Image.new('RGBA', (w, h), (255, 255, 255, 255))
        else:
            sprite = Image.new('RGB', (w, h), (255, 255, 255))
        
        for image in images:
            im = image.get('image')
            im_w = im.size[0]
            im_h = im.size[1]
            sprite.paste(im, (x_pos, y_pos))
            
            # info for producing css
            img_positions.update({image.get('name'): {'x': x_pos,
                                                      'y': y_pos,
                                                      'w': im_w,
                                                      'h': im_h,
                                                      }
                                  })
            
            x_pos += im_w
        
        sprite.save(self.sprite_path, "PNG")
        
        return img_positions
    
    def create_css(self, img_positions):
        num_levels = len([part for part in self.css_dir.split(self.curdir) if part]) 
        
        sprite_path = os.path.join(self.sprite_dir.split(self.curdir)[1], "sprites.png")
        sprite_path = sprite_path.startswith('/') and sprite_path[1:] or sprite_path
        if num_levels:
            sprite_path = "%s%s" % ("../" * num_levels, sprite_path)
        css = """.sprite {
  display: block;
  background: url('%s');
}
""" % sprite_path
        
        num_levels = len(os.path.abspath(self.css_dir).split("/")) - len(self.curdir.split("/"))
        
        for class_name, img_pos in img_positions.items():
            tmp = CSS_TPL % {'class_name': class_name,
                             'w': img_pos.get('w'),
                             'h': img_pos.get('h'),
                             'x': img_pos.get('x') * -1,
                             'y': img_pos.get('y') * -1,
                             }

            css += tmp
        cssdir = os.path.join(self.css_dir, 'sprites.css')
        
        f = open(cssdir, 'w')
        f.write(css)
        f.close()
    
    def create_html(self, class_names):
        """ Creates an html page for testing purposes """
        
        body = ""
        for class_name in class_names:
            body += "    <div class=\"sprite %s\"></div>\n" % class_name
            
        tpl = HTML_TPL % {'css_file': os.path.join(self.css_dir, "sprites.css"),
                          'body': body,
                          }
        
        f = open('sprites.html', 'w')
        f.write(tpl)
        f.close()
        
        

if __name__ == "__main__":
    
    usage = """Usage:
spriteomatic.py [image directory] [OPTIONS]
  -a, --alpha \t\t alpha channel, 0 or 1 (default=1)
  --sprite_dir \t\t output directory for sprites.png
  --css_dir \t\t output directory for css
  -h, --help \t\t display help
"""
    
    argv = sys.argv[1:]
    curdir = os.path.abspath(os.path.curdir)
    
    sprite_dir = curdir
    css_dir = curdir
    alpha = 1
    debug = True
    
    if not len(argv) or not os.path.isdir(argv[0]):
        print usage
        sys.exit(2)
    else:
        img_dir = argv[0]
    
    try:                                
        opts, args = getopt.getopt(argv[1:], "a:h", ["alpha=",
                                                     "css_dir=",
                                                     "sprite_dir=",
                                                     "help"])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print usage
            sys.exit()
            
        elif opt in ('-a', '--alpha'):
            try:
                alpha = int(arg)
            except:
                print usage
                sys.exit(2)
                
        elif opt in ('--sprite_dir'):
            if os.path.isdir(arg):
                sprite_dir = os.path.abspath(arg)
                if not sprite_dir.startswith(curdir):
                    print "sprite_dir must be under %s" % curdir
                    sys.exit(2)
            else:
                print "%s is not a valid directory" % arg
                sys.exit(2)
        
        elif opt in ('--css_dir'):
            if os.path.isdir(arg):
                css_dir = os.path.abspath(arg)
                if not css_dir.startswith(os.path.abspath(os.path.curdir)):
                    print "css_dir must be under %s" % curdir
                    sys.exit(2)
            else:
                print "%s is not a valid directory" % arg
                sys.exit(2)

                
    spriteomatic = SpriteOMatic(img_dir, sprite_dir, css_dir, alpha, debug)
    spriteomatic.run()