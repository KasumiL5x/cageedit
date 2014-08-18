import os.path
import maya.mel as mel
import maya.cmds as cmds
import apply_push_deformer as PushDeformer

class CageEdit(object):
	"""docstring for CageEdit"""
	def __init__(self):
		self.cage_name = ''
		self.cage_ext = '_cage'
	#END

	def __get_user_cage_name(self):
		# Prompt for the input
		result = cmds.promptDialog(
			title='CageEdit', message='Enter Cage Name:',
			button=['OK', 'Cancel'], defaultButton='OK',
			cancelButton='Cancel', dismissString='Cancel')
		# Handle cancel
		if result == 'Cancel':
			return None

		# Retrieve value
		value = cmds.promptDialog(query=True, text=True)
		# Safety check
		if value == None or not len(value):
			return None
		# Force valid value
		return mel.eval('formValidObjectName(\"{0}\");'.format(value))
	#END

	def __configure(self):
		# Set up the material properties
		self.mat_name = 'mat_' + self.cage_name + self.cage_ext
		self.mat_sg_name = self.mat_name + 'SG'
		self.mat_type = 'lambert'
		self.mat_color = (1.0, 0.5, 0.5, 1.0)
		self.mat_trans = (0.25, 0.25, 0.25, 0.25)

		# Set up the group properties
		self.group_name = 'grp_' + self.cage_name + self.cage_ext

		# Display layer properties
		self.layer_name = "lyr_" + self.cage_name + self.cage_ext
	#END

	def __precheck(self):
		# If the material node exists and isn't the right type...
		if cmds.objExists(self.mat_name) and cmds.nodeType(self.mat_name) != self.mat_type:
			cmds.warning('Material node already exists and isn\'t the right type.')
			return False

		# If the shading group node exists and isn't the right type...
		if cmds.objExists(self.mat_sg_name) and cmds.nodeType(self.mat_sg_name) != 'shadingEngine':
			cmds.warning('Shading group node already exists and isn\'t the right type.')
			return False

		# If the group exists and isn't the right type...
		if cmds.objExists(self.group_name) and cmds.nodeType(self.group_name) != 'transform':
			cmds.warning('Group node already exists and isn\'t the right type.')
			return False

		# If the display layer already exists and isn't the right type...
		if cmds.objExists(self.layer_name) and cmds.nodeType(self.layer_name) != 'displayLayer':
			cmds.warning('Display layer node already and isn\'t the right type.')
			return False

		return True
	#END

	def __create_mat(self):
		# If the shader doesn't exist, create it
		if not cmds.objExists(self.mat_name):
			self.mat_name = cmds.shadingNode(self.mat_type, name=self.mat_name, asShader=True)

		# Set the properties of the shader
		cmds.setAttr(self.mat_name + '.color', self.mat_color[0], self.mat_color[1], self.mat_color[2], self.mat_color[3])
		cmds.setAttr(self.mat_name + '.transparency', self.mat_trans[0], self.mat_trans[1], self.mat_trans[2], self.mat_trans[3])

		# If the shading group doesn't exist, create it
		if not cmds.objExists(self.mat_sg_name):
			self.mat_sg_name = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=self.mat_sg_name)

		# If not already connected, connect the shader and the shading group
		if not cmds.isConnected(self.mat_name + '.outColor', self.mat_sg_name + '.surfaceShader'):
			cmds.connectAttr(self.mat_name + '.outColor', self.mat_sg_name + '.surfaceShader')
	#END

	def __create_group(self):
		# If the group doesn't already exist, create it
		if not cmds.objExists(self.group_name):
			self.group_name = cmds.group(name=self.group_name, empty=True, world=True)
	#END

	def __create_layer(self):
		# If the display layer doesn't already exist, create it
		if not cmds.objExists(self.layer_name):
			self.layer_name = cmds.createDisplayLayer(name=self.layer_name, empty=True)
	#END

	def __assign_to_layer(self, cages):
		cmds.editDisplayLayerMembers(self.layer_name, cages)
	#END

	def __get_selected_transforms(self):
		meshes = cmds.ls(sl=True, type='mesh', dag=True, ap=True)
		# Return with removed meshes that contain the cage extension
		# so we don't end up accidentally caging cages...haha
		return filter(lambda x: self.cage_ext not in str(x), meshes)
	#END

	def __duplicate_meshes(self, meshes):
		cages = []
		for x in meshes:
			obj_name = x + self.cage_ext
			if cmds.objExists(obj_name):
				cmds.warning('Cage generation skipped for (' + str(x) + ') as another node already exists.')
				continue
			# Duplicate the mesh (ignoring children)
			dupe_mesh = cmds.duplicate(x, name=obj_name, rr=True)[0]
			# Parent the mesh and use this name, as it could possibly change?
			curr = cmds.parent(dupe_mesh, self.group_name, s=True)[0]
			# Hacky string to get the full path (since it's parented to world, we can assume here)
			cages.append(self.group_name + '|' + str(curr))
		return cages
	#END

	def __apply_material(self, cages):
		cmds.sets(cages, edit=True, forceElement=self.mat_sg_name)
	#END

	def __apply_push_deformer(self, cages):
		apd = PushDeformer.ApplyPushDeformer()
		apd.apply_push_deformer(cages)
	#END

	def export_cages(self):
		# Get the cage name from the user
		self.cage_name = self.__get_user_cage_name()
		if self.cage_name is None:
			cmds.warning('Export canceled by the user.')
			return
		# Configure based on the name given by the user
		self.__configure()

		# Warn the user about order
		warning_result = cmds.confirmDialog(
			title='CageEdit', message='Note, the order of the cage meshes in the outliner MUST be identical to the order of the corresponding geometry.  Continue?',
			icon='information', button=['OK', 'Cancel'], dismissString='Cancel')
		if warning_result == 'Cancel':
			return

		# If the group doesn't exist, don't export
		if not cmds.objExists(self.group_name):
			cmds.warning('Export canceled as the cages\' group node was not found.')
			return

		# Get all child meshes
		children = cmds.listRelatives(self.group_name)
		if children is None or not len(children):
			cmds.warning('Export canceled as the cages\' group has no children.')
			return

		# Ask the user for a file
		out_file = cmds.fileDialog2(fileFilter='OBJ (*.obj) (*.obj)', dialogStyle=2, cap='Export to...')
		if out_file is None:
			cmds.warning('Export canceled by the user.')
			return

		# Clear the selection
		cmds.select(clear=True)
		# Select all children meshes
		for x in children:
			cmds.select(x, add=True)

		# If the output file doesn't already exist, create it
		if not os.path.isfile(out_file[0]):
			open(out_file[0], 'w+')

		# Export the file
		cmds.file(out_file[0], exportSelected=True,
			constructionHistory=False, channels=False,
			constraints=False, expressions=False,
			shader=False, force=True, type='OBJ', )

		cmds.warning('Exported cages.')
	#END

	def delete_cages(self):
		# Open undo chunk
		cmds.undoInfo(openChunk=True)

		# Get the cage name from the user
		self.cage_name = self.__get_user_cage_name()
		if self.cage_name is None:
			cmds.warning('Delete canceled by user.')
			return

		# Warn the user it will delete, just to be safe
		warning_result = cmds.confirmDialog(
			title='CageEdit', message='Are you sure you want to delete this cage?',
			icon='warning', button=['OK', 'Cancel'], dismissString='Cancel')
		if warning_result == 'Cancel':
			return

		# Configure based on the name given by the user
		self.__configure()

		# Group (and subsequently, meshes below it)
		if cmds.objExists(self.group_name):
			cmds.delete(self.group_name)
		else:
			cmds.warning('Ignored group and cages, as the group node doesn\'t exist.')

		# Display layer
		if cmds.objExists(self.layer_name):
			cmds.delete(self.layer_name)
		else:
			cmds.warning('Ignored display layer as the node doesn\'t exist.')

		# Shader
		if cmds.objExists(self.mat_name):
			cmds.delete(self.mat_name)
		else:
			cmds.warning('Ignored material as the node doesn\'t exist.')

		# Shading group
		if cmds.objExists(self.mat_sg_name):
			cmds.delete(self.mat_sg_name)
		else:
			cmds.warning('Ignored shading group as the node doesn\'t exist.')

		cmds.warning('Deleted cages.')

		# Close undo chunk
		cmds.undoInfo(closeChunk=True)
	#END

	def generate_cages(self):
		# Open undo chunk
		cmds.undoInfo(openChunk=True)

		meshes = self.__get_selected_transforms()
		if not len(meshes):
			cmds.warning('Nothing selected.')
			# Close undo chunk
			cmds.undoInfo(closeChunk=True)
			return

		# Get the cage name from the user
		self.cage_name = self.__get_user_cage_name()
		if self.cage_name is None:
			cmds.warning('Generation canceled by user.')
			return
		# Configure based on the name given by the user
		self.__configure()
		# Run a quick check
		if not self.__precheck():
			# Close undo chunk
			cmds.undoInfo(closeChunk=True)
			return
		# Create the cage material
		self.__create_mat()
		# Create the group cages will be parented to
		self.__create_group()
		# Create the display layer the objects will be assigned to
		self.__create_layer()
		# Create the actual cage geometry
		cages = self.__duplicate_meshes(meshes)
		# Check cages were generated (e.g. skipped due to already existing)
		if not len(cages):
			cmds.warning('No cages generated.')
			# Close undo chunk
			cmds.undoInfo(closeChunk=True)
			return
		# Apply the cage material
		self.__apply_material(cages)
		# Assign the cages to the display layer
		self.__assign_to_layer(cages)
		# Apply push deformer to all cages
		self.__apply_push_deformer(cages)

		cmds.warning('Generated cages.')

		# Close undo chunk
		cmds.undoInfo(closeChunk=True)
	#END
#END
