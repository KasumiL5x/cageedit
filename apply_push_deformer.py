import maya.mel as mel
import maya.cmds as cmds

class ApplyPushDeformer(object):
	def __init__(self):
		pass

	def __load_plugin(self):
		if not cmds.pluginInfo('push_deformer.py', l=True, q=True):
			if cmds.loadPlugin('push_deformer.py') == None:
				cmds.warning('Failed to load plugin.')
				return False
		return True
	#END

	def __apply(self, mesh):
		print 'selecting ' + str(mesh)
		cmds.select(mesh)
		name = str(mesh) + '_pushDeformer'
		name = mel.eval('formValidObjectName(\"{0}\");'.format(name))
		cmds.deformer(name=name, type='pushDeformer')
	#END

	def apply_push_deformer(self, meshlist):
		if not self.__load_plugin():
			return

		for x in meshlist:
			self.__apply(x)
	#END
		
	def apply_push_deformer_selection():
		if not self.__load_plugin():
			return

		objs = cmds.ls(sl=True, type='transform')
		if not len(objs):
			cmds.warning('No objects selected.')
			return

		for x in objs:
			cmds.select(x)
			name = str(x) + '_pushDeformer'
			name = mel.eval('formValidObjectName(\"{0}\");'.format(name))
			cmds.deformer(name=name, type='pushDeformer')
	#END
#END
