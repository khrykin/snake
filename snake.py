import dxfwrite
from dxfwrite import DXFEngine as dxf

# Layer names
class Layers:
	substrate = 'SUBSTRATE'
	pads = 'PADS'
	snake = 'SNAKE'

# Builds dxf file according to input parameters. 
# All sizes are in mm.
def draw(
	filename = 'Untitled.dxf',
	substrate_size = 10.0,

	height = 5.5,
	pad_size = 1.0,
	pads_neck_size = 0.2,

	number_of_loops = 200,
	snake_thickness = 0.005, # 5 um
	snake_loop_margin = 0.5,
	snake_pads_offset = 0.5
):
	# MARK: - Configuration

	drawing = dxf.drawing(filename)

	# Computed variables
	WIDTH = height
	SUBSTRATE_Y_EXTRA_SHIFT = height / substrate_size

	# Pads
	PADS_GAP_SIZE = 0.33 * pad_size

	PADS_GROUP_SIZE = 2 * pad_size + PADS_GAP_SIZE
	PADS_TOTAL_SIZE = 2 * PADS_GROUP_SIZE + PADS_GAP_SIZE

	PADS_ORIGIN_X = (WIDTH - PADS_TOTAL_SIZE) / 2

	# Snake
	GAP = WIDTH / number_of_loops - snake_thickness
	SNAKE_WIDTH = WIDTH

	SNAKE_ORIGIN = (
		PADS_ORIGIN_X + PADS_GROUP_SIZE - snake_thickness / 2,
		pad_size
	)

	SNAKE_PADS_EXTENT = (SNAKE_WIDTH - PADS_GAP_SIZE) / 2

	SNAKE_LEFT_CORNER = (
		SNAKE_ORIGIN[0] - SNAKE_PADS_EXTENT + snake_thickness,
		SNAKE_ORIGIN[1] + snake_pads_offset
	)

	SNAKE_RIGHT_CORNER = (
		SNAKE_ORIGIN[0] + SNAKE_PADS_EXTENT + PADS_GAP_SIZE,
		height - snake_thickness / 2
	)

	SNAKE_LOOPS_GAP = (SNAKE_WIDTH - snake_thickness) / (2 * number_of_loops + 1)

	# Substrate
	SUSTRATE_SHIFT_X = (substrate_size - WIDTH) / 2
	SUSTRATE_SHIFT_Y = (substrate_size - height) / 2 - SUBSTRATE_Y_EXTRA_SHIFT

	# MARK: - Paths

	# Chip substrate bounds
	substrate_points = [
		(-SUSTRATE_SHIFT_X, -SUSTRATE_SHIFT_Y),
		(substrate_size - SUSTRATE_SHIFT_X, -SUSTRATE_SHIFT_Y),
		(substrate_size - SUSTRATE_SHIFT_X, substrate_size -SUSTRATE_SHIFT_Y),
		(-SUSTRATE_SHIFT_X, substrate_size - SUSTRATE_SHIFT_Y),
		(-SUSTRATE_SHIFT_X, -SUSTRATE_SHIFT_Y)
	]

	# Bounding loop of snake
	snake_main_loop = [
		SNAKE_ORIGIN,
		(SNAKE_ORIGIN[0], SNAKE_LEFT_CORNER[1]),
		SNAKE_LEFT_CORNER,
		(SNAKE_LEFT_CORNER[0], height - snake_thickness / 2),
		SNAKE_RIGHT_CORNER,
		(SNAKE_RIGHT_CORNER[0], SNAKE_LEFT_CORNER[1]),
		(SNAKE_ORIGIN[0] + PADS_GAP_SIZE + snake_thickness, SNAKE_LEFT_CORNER[1]),
		(SNAKE_ORIGIN[0] + PADS_GAP_SIZE + snake_thickness, SNAKE_ORIGIN[1]),
	]

	# Injects snake points into snake_main_loop
	def inject_snake_into(snake_main_loop):
		snake_start = snake_main_loop[0:4]
		snake_end = snake_main_loop[4:8]

		snake_points = snake_start

		# Adds loops to snake_main_loop
		for i in range(1, number_of_loops + 1):
			bottom_l_x = SNAKE_LEFT_CORNER[0] + (2 * i - 1) * SNAKE_LOOPS_GAP
			bottom_y = SNAKE_LEFT_CORNER[1] + snake_loop_margin
			loop_points = [
				(bottom_l_x, height - snake_thickness / 2),
				(bottom_l_x, bottom_y),
				(bottom_l_x + SNAKE_LOOPS_GAP, bottom_y),
				(bottom_l_x + SNAKE_LOOPS_GAP, height - snake_thickness / 2)
			]

			snake_points = snake_points + loop_points

		return snake_points + snake_end
	
	# The whole snake path
	snake_points = inject_snake_into(snake_main_loop)

	# Returns points for two pads for given origin
	def pads_points(origin = (0, 0)):
		height = origin[1] + pad_size
		return [
			origin,
			(origin[0], height),
			(origin[0] + PADS_GROUP_SIZE, height),
			(origin[0] + PADS_GROUP_SIZE, origin[1]),
			(origin[0] + PADS_GROUP_SIZE - pad_size, origin[1]),
			(origin[0] + PADS_GROUP_SIZE - pad_size, height - pads_neck_size),
			(origin[0] + pad_size, height - pads_neck_size),
			(origin[0] + pad_size, origin[1]),
			origin
		]

	left_pads_points = pads_points((PADS_ORIGIN_X, 0))
	right_pads_points = pads_points((PADS_ORIGIN_X + PADS_GROUP_SIZE + PADS_GAP_SIZE, 0))
	
	# Left lead wire
	left_lead_points = [
		left_pads_points[4],
		left_pads_points[3],
		(snake_main_loop[1][0], snake_main_loop[1][1] + pads_neck_size),
		(
			snake_main_loop[2][0] + pads_neck_size, 
			snake_main_loop[2][1] + pads_neck_size
			),
		(
			snake_main_loop[2][0] + 2 * snake_thickness, 
			snake_main_loop[2][1] + (snake_loop_margin - pads_neck_size / 2)
		),
		(
			snake_main_loop[2][0] - 2 * snake_thickness,
			snake_main_loop[2][1] + (snake_loop_margin - pads_neck_size / 2)
		),
		(
			snake_main_loop[2][0] - 2 * snake_thickness,
			snake_main_loop[2][1]
		),
		(
			snake_main_loop[1][0] - pads_neck_size,
			snake_main_loop[1][1]
		),
		(
			snake_main_loop[0][0] - pads_neck_size,
			snake_main_loop[0][1]
		),
		(left_pads_points[2][0] - pad_size, left_pads_points[2][1]),
		left_pads_points[4]
	]

	# Reflects points along x axis
	def reflect_x(points, x_axis):
		return list(map(lambda point: 
			(2 * x_axis - point[0], point[1]),
			points
		))

	right_lead_points = reflect_x(
		left_lead_points, 
		left_lead_points[1][0] + PADS_GAP_SIZE / 2
	)

	# MARK: - Drawing objects

	substrate = dxf.polyline(
		substrate_points,
		layer=Layers.substrate,
		flags=0
	)

	snake = dxf.polyline(
		snake_points,
		layer=Layers.snake,
		flags=0,
		startwidth=snake_thickness,
		endwidth=snake_thickness,
	)

	left_pads = dxf.polyline(
		left_pads_points,
		layer=Layers.pads,
		flags=0
	)

	right_pads = dxf.polyline(
		right_pads_points,
		layer=Layers.pads,
		flags=0
	)

	left_leads = dxf.polyline(
		left_lead_points,
		layer=Layers.snake,
		flags=0
	)

	right_leads = dxf.polyline(
		right_lead_points,
		layer=Layers.snake,
		flags=0
	)

	# MARK: - Drawing
	drawing.add_layer(Layers.substrate, color=1)
	drawing.add_layer(Layers.pads, color=2)
	drawing.add_layer(Layers.snake, color=7)

	drawing.add(substrate)
	drawing.add(snake)

	# Left pads
	drawing.add(left_pads)

	# Right pads
	drawing.add(right_pads)

	# Left leads
	drawing.add(left_leads)
	
	# Right leads
	drawing.add(right_leads)

	drawing.save()