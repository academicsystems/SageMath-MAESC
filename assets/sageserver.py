#!/opt/sage/sage -python

import warnings
warnings.filterwarnings("ignore")

import json
import mimetypes
import os
import random
import re
import web
import string
import time
import zipfile
from types import ModuleType
from sage.all import *

# functions for users

# this function will attempt to save the object so that it can be retrieved later
def save(obj,fileext='.png',options={}):
    images_2d = ['.bmp','.png','.gif','.ppm','.tiff','.tif','.jpg','.jpeg']
    images_3d_static = ['.x3d','.stl','.amf','.ply','.canvas3d']
    images_3d_dynamic = ['.threejs','.jmol'] # these produce javascript files
    all_images = images_2d + images_3d_static + images_3d_dynamic
    
    # for allowing the use of for example 'png' or '.png'
    if fileext[0] != '.':
        fileext = '.' + fileext
    
    if fileext not in all_images:
        filelist.append([fileext + ' not supported. These are supported: ' + ','.join(all_images)])
    
    # check class, only sage.plot.graphics... objects can be rendered to images
    objclass = str(type((obj))).split("'")[1].split('.')
    if objclass[0] != 'sage' or objclass[1] != 'plot' or objclass[2] != 'graphics':
        return 'error. trying to save non graphics image.'
    
    if fileext in images_2d:
        filename = tmp_filename(name='tmp_', ext=fileext)
        obj.save(filename)
        return filename.split('/')[-1]
    
    if fileext == '.canvas3d':
        filename = tmp_filename(name='tmp_', ext='.canvas3d')
        obj._rich_repr_canvas3d().canvas3d.save_as(filename)
        return filename.split('/')[-1]
    
    # this is for wavefront, but it produces 2 files, so it has been disabled above
    if fileext == '.wavefront':
        objfilename = tmp_filename(name='tmp_', ext='.obj')
        mtlfilename = tmp_filename(name='tmp_', ext='.mtl')
        wf = obj._rich_repr_wavefront()
        wf.obj.save_as(objfilename)
        wf.mtl.save_as(mtlfilename)
        # !! should save this together as a zip file and return that
        return 'error. not-available'
    
    if fileext in images_3d_static:
        filename = tmp_filename(name='tmp_', ext=fileext)
        obj.save(filename)
        return filename.split('/')[-1]
    
    # requires these files to run this script:
    # <script src="https://cdn.rawgit.com/mrdoob/three.js/r80/build/three.min.js"></script>
    # <script src="https://cdn.rawgit.com/mrdoob/three.js/r80/examples/js/controls/OrbitControls.js"></script>
    # var tjsdiv should be set to the div that should append the 3d image. if not set, will default to document.body
    # this is currently limited to one image per page
    if fileext == '.threejs':
        filename = tmp_filename(name='tmp_', ext='.js')
        tjs_script = re.split('</script>',re.split('<script>',obj._rich_repr_threejs().html._data)[1])[0]
        
        if 'divid' in options:
            tjs_final = 'var tjsdiv = document.getElementById("' + options['divid'] + '"); ' + tjs_script.replace('document.body','tjsdiv')
        else:
            tjs_final = 'if (typeof tjsdiv === "undefined") { var tjsdiv = document.body; } ' + tjs_script.replace('document.body','tjsdiv')
        
        with open(filename, "w") as text_file:
            text_file.write("%s" % tjs_final)
        
        return filename.split('/')[-1]
    
    # requires these files to run this script:
    # <script src="https://cdn.jsdelivr.net/jsmol/14.6.2/JSmol.min.js"></script>
    # ... still need j2s folder of files
    if fileext == '.jmol':
        filename = tmp_filename(name='tmp_', ext='.js')

        file = tmp_filename(name='tmp_', ext='.jmol')
        obj.export_jmol(file)
        
        jmolscript = zipfile.ZipFile(file).read('SCRIPT')
        
        # create applet info optional parameters
        AppletInfo = {}
        AppletInfo['color'] = options['color'] if 'color' in options else "#FFFFFF"
        AppletInfo['height'] = options['height'] if 'height' in options else 300
        AppletInfo['width'] = options['width'] if 'width' in options else 300
        AppletInfo['j2sPath'] = options['j2sPath'] if 'j2sPath' in options else "j2s"
        
        AppletInfo['script'] = 'AppletScript'
        AppletInfo['use'] = "HTML5"
        AppletInfo['disableInitialConsole'] = True
        
        AppletName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        jsmolscript = "var AppletScript = `" + jmolscript + "`; " + "if (typeof AppletInfo === 'undefined') { var AppletInfo = " + json.dumps(AppletInfo) + " }; Jmol.getApplet('" + AppletName + "', AppletInfo);"
        
        with open(filename, "w") as text_file:
            text_file.write("%s" % zipfile.ZipFile(file).read('SCRIPT'))
        return filename.split('/')[-1]

# helper functions

def sage_exec(sagestr):
    try:
        exec(preparse(sagestr))
    except IOError as e:
        error = 'Error, you must use save(object,fileext,options) function to save sagemath images'
    except Exception as e:
        error = str(e)
    del sagestr
    lvars = locals()
    sagevars = {}
    for key, obj in lvars.iteritems():
        if not isinstance(obj,ModuleType):
            sagevars[key] = obj
    return sagevars

def filter_vars(sagevars,reqkeys):
    reqvars = {}
    for key in reqkeys:
        if key in sagevars:
            reqvars[key] = sagevars[key]
        else:
            reqvars[key] = ''
    return reqvars

# web routes

mimetypes.init()

class Main:
    def POST(self):
        # get post request json body
        try:
            data = json.loads(web.data())
        except:
            respdict = {'error':'json is not formatted correctly'}
            return json.dumps(respdict)
        
        # execute sage commands
        try:
            sagevars = sage_exec(data['code'])
        except Exception as e:
            respdict = {'error':str(e)}
            return json.dumps(respdict)
        
        # get requested variables
        reqvars = filter_vars(sagevars,data['vars'])
        
        respdict = {}
        for key, value in reqvars.iteritems():
            if key[0] != "_":
                respdict[key] = [str(value),latex(value)]
            else:
                respdict[key] = [value]
        
        return json.dumps(respdict)

class TestConnection:
    def GET(self):
        startTime = time.time()
        sage_exec('x = 1')
        totalTime = time.time() - startTime
        respdict = {'Sage Exec Time':totalTime}
        return json.dumps(respdict)

# /service => responds with {regvar:["text","latex"],filevar:["filename"]} etc.
if __name__ == "__main__":
    tmpfpath = tmp_filename(name='1234567890qwerty', ext='.txt')
    SAGE_TMP_DIR = tmpfpath.split('1234567890qwerty')[0]
    if os.path.exists('/var/www/static'):
        os.unlink('/var/www/static')
    try:
        os.symlink(SAGE_TMP_DIR,'/var/www/static')
    except:
        pass
    
    urls = (
          '/service', 'Main',
          '/', 'TestConnection'
        )
    app = web.application(urls, globals())
    app.run()

