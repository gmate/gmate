'''
Retrieve dimensions of an image from file
@author Sergey Chikuyonok (serge.che@gmail.com)
@link http://chikuyonok.ru

Changes for Gedit Plugin
@author Franck Marcia (franck.marcia@gmail.com)
@link http://github.com/fmarcia/zen-coding-gedit
'''

from subprocess import Popen, PIPE
import urllib
import os
import re
import zen_file, zen_core

def replace_or_append(img_tag, attr_name, attr_value):
    """
    Replaces or adds attribute to the tag
    @type img_tag: str
    @type attr_name: str
    @type attr_value: str
    """
    if attr_name in img_tag.lower():
        # attribute exists
        re_attr = re.compile(attr_name + r'=([\'"])(.*?)\1', re.I)
        return re.sub(re_attr, lambda m: '%s=%s%s%s' % (attr_name, m.group(1), attr_value, m.group(1)), img_tag)
    else:
        return re.sub(r'\s*(\/?>)$', ' ' + attr_name + '="' + attr_value + r'" \1', img_tag)

def find_image(editor):
    """
    Find image tag under caret
     @return Image tag and its indexes inside editor source
    """
    _caret = editor.get_caret_pos()
    text = editor.get_content()
    start_ix = -1
    end_ix = -1
    
    # find the beginning of the tag
    caret_pos = _caret
    while caret_pos >= 0:
        if text[caret_pos] == '<':
            if text[caret_pos:caret_pos + 4].lower() == '<img':
                # found the beginning of the image tag
                start_ix = caret_pos
                break
            else:
                # found some other tag
                return None
        caret_pos -= 1
            
    # find the end of the tag 
    caret_pos = _caret
    ln = len(text)
    while caret_pos <= ln:
        if text[caret_pos] == '>':
            end_ix = caret_pos + 1
            break
        caret_pos += 1
    
    
    if start_ix != -1 and end_ix != -1:
        return {
            'start': start_ix,
            'end': end_ix,
            'tag': text[start_ix:end_ix]
        }
    
    return None

def get_image_size(editor, img):
    """
    Returns size of image in <img>; tag
     @param img: Image tag
    @return Dictionary with <code>width</code> and <code>height</code> attributes
    """
    m = re.search(r'src=(["\'])(.+?)\1', img, re.IGNORECASE)
    if m:
        src = get_absolute_uri(editor, m.group(2))
        if not src:
            return None
        try:
            content = zen_file.read(src)
            return zen_core.get_image_size(content)
        except:
            pass
        
    return None

def get_absolute_uri(editor, img_path):
    file_uri = editor.document.get_uri()
    if not file_uri: return None
    file_uri = re.sub(r'^file://', '', file_uri)
    
    if img_path[0] == '/':
        img_path = img_path[1:]
    
    while True:
        head, tail = os.path.split(file_uri)
        if not head or head == '/': break # reached the top
            
        abs_image_path = os.path.join(head, img_path)
        abs_image_path = os.path.normpath(abs_image_path)
        if os.path.exists(abs_image_path):
            return os.path.join(abs_image_path)
        
        if head == file_uri: break # infinite loop protection
        file_uri = head
        
    return None

def update_image_size(editor):
    image = find_image(editor)
    if image:
        size = get_image_size(editor, image['tag'])
        if size:
            new_tag = replace_or_append(image['tag'], 'width', size['width'])
            new_tag = replace_or_append(new_tag, 'height', size['height'])
            editor.replace_content(new_tag, image['start'], image['end'])
