# Name: Team 1
# Description: Software Engineering Project
# Date: Fall 2025

import pygame
import time
import psycopg2

from pygame.locals import*
from time import sleep
from psycopg2 import sql
from udp_handler import UdpHandler
from python_udpclient import PythonUdpClient

# Screen indices - used to switch view between screens
splash_index = 0
player_screen_index = 1
game_screen_index = 2

# Sleep time - How long until next frame
sleep_time = 0.04

# Default Network IP Address
default_network = "127.0.0.1"

class Player():
	def __init__(self, id, code_name, equip_id):
		self.id = id
		self.code_name = code_name
		self.equip_id = equip_id

# Used to display player information; receives coordinates, dimensions, and a string to display
class Box():
	def __init__(self, x, y, w, h, text):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.text_box = pygame.Rect(x, y, w, h)
		self.text = text

# Used to display/receive information to/from user, primarily in adding players
class Popup(Box):
	def __init__(self, x, y, w, h, text, input_box_x, input_box_y, input_box_w, input_box_h, popup):
		super().__init__(x, y, w, h, text)
		self.input_box_x = input_box_x
		self.input_box_y = input_box_y
		self.input_box_w = input_box_w
		self.input_box_h = input_box_h
		self.input_box = pygame.Rect(input_box_x, input_box_y, input_box_w, input_box_h)
		# Show feedback of what user enters
		self.input_feedback = ""
		# boolean to determine when popup displays
		self.popup = popup

# Used to display input information (What the funct keys do); have multiple lines to display information
class Funct_Box(Box):
	def __init__(self, x, y, w, h, text, text2, text3):
		super().__init__(x, y, w, h, text)
		self.text2 = text2
		self.text3 = text3

class Model():
	def __init__(self):
		# Start game with splash screen
		self.screen_index = splash_index
		# Timer used to change from splash screen to player entry screen
		self.splash_timer = 0
		# Arrays of Players
		self.red_players = []
		self.green_players = []
		self.num_players_per_team = 15
		# Counters to keep track of players per team
		self.num_red_players = 0
		self.num_green_players = 0

		# Adding player booleans
		self.need_id = True
		self.need_code_name = False
		# self.need_equip_id = True

		# Temporary player creation variables
		self.temp_id = -1
		self.temp_code_name = ""

		# Creating Required SQL DB connections
		connection_params = {
			'dbname': 'photon',
  			'user': 'student',
		}

		self.conn = psycopg2.connect(**connection_params)
		self.cursor = self.conn.cursor()

		# If game is currently in progress
		self.game_active = False
		# Game timer
		self.game_timer = 0
		# Length of game (in seconds)
		self.game_length = 10

		# Initialize Arrays
		i = 0
		while (i < self.num_players_per_team):
			self.red_players.append(Player("", "", ""))
			self.green_players.append(Player("", "", ""))
			i += 1
		
		# Network IP + UDP TX
		self.network = default_network
		self.udp_tx = PythonUdpClient(dest_ip=self.network, dest_port=7500, enable_broadcast=True)

	def update(self):
		# Update timer until 3 seconds have passed
		if (self.splash_timer < (3 / sleep_time)):
			self.splash_timer += 1
		else:
			# Display player entry screen
			if (self.game_active == False):
				self.screen_index = player_screen_index
			# Display game screen until game is over
			if (self.game_active == True):
				self.screen_index = game_screen_index
				if (self.game_timer < (self.game_length / sleep_time)):
					self.game_timer += 1
				else:
					self.game_active = False
					# Clear players
					self.clear_players()
	
	def display_red_players(self):
		print("Displaying Red Team:")
		i = 0
		while ((str(self.red_players[i].id) != "") and (i < self.num_players_per_team)):
			print(str(self.red_players[i].id) + ", " + self.red_players[i].code_name)
			i += 1
	
	def display_green_players(self):
		print("Displaying Green Team:")
		i = 0
		while ((str(self.green_players[i].id) != "") and (i < self.num_players_per_team)):
			print(str(self.green_players[i].id) + ", " + self.green_players[i].code_name)
			i += 1
	
	# Check entered id against database; if found, use in table; else, prompt for equipment id
	def check_id(self, id):
		# Convert id to non-negative integer
		if (id < 0):
			id *= -1
		# Convert id to integer between 0 and 99
		id = id % 100

		self.temp_id = id
		# Check if id is in database; if in, set temp_code_name to code name in database
		sql_query = "SELECT * FROM players WHERE id = %s;"
		self.cursor.execute(sql_query, (id,))
		rows = self.cursor.fetchall()
		# Set this to failure and then change it if we succeed
		self.need_code_name = True
		# rows evaluates to true if there is anything in the list, and the only element in the list must be the correct tuple
		if (rows):
			self.temp_code_name = rows[0][1] 
			self.need_code_name = False
		self.cursor.execute("SELECT * FROM players")
		print("Current SQL contents (before insertion of current id):")
		rows = self.cursor.fetchall()
		for row in rows:
			print(row)

		

	# Enter code name into database
	def enter_code_name(self, code_name):
#		# Enter id and code name into database
		sql_query = "INSERT INTO players (id, codename) VALUES (%s, %s);"
		self.cursor.execute(sql_query,(self.temp_id, code_name))
		self.conn.commit()
		# create temporary code name
		self.temp_code_name = code_name

	def add_player(self, equip_id):
		# Put in team based on equipment id (Odd -> Red; Even -> Green)
		if ((equip_id % 2 == 1) and (self.num_red_players <= self.num_players_per_team)): # Do not add a player if there are already 15
			self.red_players[self.num_red_players].id = self.temp_id
			self.red_players[self.num_red_players].code_name = self.temp_code_name
			self.red_players[self.num_red_players].equip_id = equip_id
			self.num_red_players += 1 
			# Broadcast player id
			try:
				self.udp_tx.send_int(equip_id)
			except Exception as e:
				print(f"UDP send failed: {e}")
		
		elif ((equip_id % 2 == 0) and (self.num_green_players <= self.num_players_per_team)): # Do not add a player if there are already 15
			self.green_players[self.num_green_players].id = self.temp_id
			self.green_players[self.num_green_players].code_name = self.temp_code_name
			self.green_players[self.num_green_players].equip_id = equip_id
			self.num_green_players += 1
			# Broadcast player id
			try:
				self.udp_tx.send_int(equip_id)
			except Exception as e:
				print(f"UDP send failed: {e}")
				
	def clear_players(self):
		i = 0
		while (i < self.num_players_per_team):
			self.red_players[i].id = ""
			self.red_players[i].code_name = ""
			self.green_players[i].id = ""
			self.green_players[i].code_name = ""
			i += 1
		self.num_red_players = 0
		self.num_green_players = 0
	
	def start_game(self):
		print("Starting game")
		# Switch screen index to show game screen
		self.game_active = True
		# Game code
#
	
#	# Change Network IP
	def change_network(self, network):
		self.network = network
		try:
			self.udp_tx.set_destination(network, 7500)
		except Exception as e:
			print(f"Failed to set UDP destination: {e}")

class View():
	def __init__(self, model):
		# Set screen size
		self.screen_w = 1000
		self.screen_h = 700
		screen_size = (self.screen_w,self.screen_h)
		self.screen = pygame.display.set_mode(screen_size, 32)
		self.model = model

		# Create popup boxes
		self.popup_box_w = 375
		self.popup_box_h = 150
		self.popup_box_x = self.screen_w/2 - self.popup_box_w/2
		self.popup_box_y = self.screen_h/2 - self.popup_box_h/2
		self.popup_input_x = self.popup_box_x + self.popup_box_w/4
		self.popup_input_y = self.popup_box_y + self.popup_box_h/2
		self.popup_input_w = self.popup_box_w/2
		self.popup_input_h = self.popup_box_h/4
		self.popup_font_size = 30
		self.popup_font = pygame.font.Font(None, self.popup_font_size)  # Default font

		self.network_popup_box = Popup(self.popup_box_x, self.popup_box_y, self.popup_box_w, self.popup_box_h, "Enter Network IP: ", self.popup_input_x, self.popup_input_y, self.popup_input_w, self.popup_input_h, False)
		self.id_popup_box = Popup(self.popup_box_x, self.popup_box_y, self.popup_box_w, self.popup_box_h, "Enter Player Id (0 - 99): ", self.popup_input_x, self.popup_input_y, self.popup_input_w, self.popup_input_h, False)
		self.code_name_popup_box = Popup(self.popup_box_x, self.popup_box_y, self.popup_box_w, self.popup_box_h, "Id Unknown. Enter Code Name: ", self.popup_input_x, self.popup_input_y, self.popup_input_w, self.popup_input_h, False)
		self.equip_id_popup_box = Popup(self.popup_box_x, self.popup_box_y, self.popup_box_w, self.popup_box_h, "Please Enter Equipment Id: ", self.popup_input_x, self.popup_input_y, self.popup_input_w, self.popup_input_h, False)

		# Colors
		self.red = (50, 0, 0)
		self.green = (0, 50, 0)
		self.white = (255, 255, 255)
		self.black = (0, 0, 0)

		# Load Splash Image
		self.splash_background = pygame.image.load("images/logo.jpg")
		self.splash_location = (0,0)
		self.splash_size = (self.screen_w, self.screen_h)
		self.scaled_splash_image = pygame.transform.scale(self.splash_background, self.splash_size)

		# Edit current game text
		self.edit_title_font_size = 45
		self.edit_title_font = pygame.font.Font(None, self.edit_title_font_size)  # Default font
		self.edit_title_text = "EDIT CURRENT GAME"

		# Red/Green Block Dimensions
		self.block_w = 350
		self.block_h = 550
		# Distance between the two blocks
		self.block_distance = 20
		# Additional Distance between top of block and top of screen
		self.top_block_offset = -30
		# Box Coordinates
		self.red_block_x = self.screen_w/2 - self.block_w - self.block_distance/2
		self.red_block_y = self.screen_h/2 - self.block_h/2 + self.top_block_offset
		self.green_block_x = self.screen_w/2 + self.block_distance/2
		self.green_block_y = self.screen_h/2 - self.block_h/2 + self.top_block_offset
		
		# Team boxes
		self.red_block = pygame.Rect(self.red_block_x, self.red_block_y, self.block_w, self.block_h)
		self.green_block = pygame.Rect(self.green_block_x, self.green_block_y, self.block_w, self.block_h)

		# Create team block titles
		self.block_title_w = self.block_w/2
		self.block_title_h = self.block_h/25
		self.red_block_title_x = self.red_block_x + self.block_w/4
		self.red_block_title_y = self.red_block_y + 5
		self.green_block_title_x = self.green_block_x + self.block_w/4
		self.green_block_title_y = self.green_block_y + 5
		self.red_block_title_box = pygame.Rect(self.red_block_title_x, self.red_block_title_y, self.block_title_w, self.block_title_h)
		self.green_block_title_box = pygame.Rect(self.green_block_title_x, self.green_block_title_y, self.block_title_w, self.block_title_h)
		self.red_block_title = "RED TEAM"
		self.green_block_title = "GREEN TEAM"
		self.block_title_font_size = 20
		self.block_title_font = pygame.font.Font(None, self.block_title_font_size)  # Default font

		# Id Box Dimensions
		self.id_box_w = 32
		self.box_h = 32
		# Distance between each id/code name box
		self.box_distance = 2
		# Id Box Initial Coordinates
		self.id_box_x = self.red_block_x + 50
		self.box_y = self.red_block_y + 30
		self.font_size = 32
		self.font = pygame.font.Font(None, self.font_size)  # Default font

		# Code name Box Dimensions
		self.code_name_box_w = 200
		# Code name Box Initial Coordinates
		self.code_name_box_x = self.id_box_x + self.id_box_w + 5

		# Create arrays of red id/code name boxes
		i = 0
		self.num_boxes = 15
		self.red_id_boxes = []
		self.red_code_name_boxes = []
		while (i < self.num_boxes):
			self.red_id_boxes.append(Box(self.id_box_x, self.box_y, self.id_box_w, self.box_h, str(self.model.red_players[i].id)))
			self.red_code_name_boxes.append(Box(self.code_name_box_x, self.box_y, self.code_name_box_w, self.box_h, str(self.model.red_players[i].code_name)))
			self.box_y += self.box_distance + self.box_h
			i += 1
		
		# Reset box values to be used for green box
		self.box_y = self.green_block_y + 30
		self.id_box_x = self.green_block_x + 50
		self.code_name_box_x = self.id_box_x + self.id_box_w + 5
		
		# Create arrays of green id/code name boxes
		i = 0
		self.green_id_boxes = []
		self.green_code_name_boxes = []
		while (i < self.num_boxes):
			self.green_id_boxes.append(Box(self.id_box_x, self.box_y, self.id_box_w, self.box_h, str(self.model.green_players[i].id)))
			self.green_code_name_boxes.append(Box(self.code_name_box_x, self.box_y, self.code_name_box_w, self.box_h, str(self.model.green_players[i].code_name)))
			self.box_y += self.box_distance + self.box_h
			i += 1

		# Create input information boxes
		self.funct_font_size = 12
		self.funct_font = pygame.font.Font(None, self.funct_font_size)  # Default font
		self.num_funct_keys = 12
		self.funct_keys_boxes = []
		self.funct_keys_boxes_w = self.screen_h/self.num_funct_keys * 1.4
		self.funct_keys_boxes_h = self.funct_keys_boxes_w
		self.funct_keys_boxes_x = (self.screen_w - self.funct_keys_boxes_w * self.num_funct_keys)/2
		self.funct_keys_boxes_y = self.screen_h - self.funct_keys_boxes_h
		# F1 - Add Player
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"F1","Add","Player"))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F2 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F3 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F4 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F5 - Start Game
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"F5","Start","Game"))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F6 - Change Network IP
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"F6","Edit","Network IP"))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F7 - Reset Network IP
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"F7","Reset IP","To Default"))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F8 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F9 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F10 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F11 - None
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"","",""))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w
		# F12 - Clear Players
		self.funct_keys_boxes.append(Funct_Box(self.funct_keys_boxes_x,self.funct_keys_boxes_y,self.funct_keys_boxes_w,self.funct_keys_boxes_h,"F12","Clear","Players"))
		self.funct_keys_boxes_x += self.funct_keys_boxes_w

	def update(self):
		# Update Text boxes
		i = 0
		while (i < self.num_boxes):
			self.red_id_boxes[i].text = str(self.model.red_players[i].id)
			self.red_code_name_boxes[i].text = str(self.model.red_players[i].code_name)
			self.green_id_boxes[i].text = str(self.model.green_players[i].id)
			self.green_code_name_boxes[i].text = str(self.model.green_players[i].code_name)
			i += 1
		# Draw background
		background_color = self.black
		self.screen.fill(background_color) # Redraw background
		# Draw screen depending on if in screen mode
		# Draw splash screen
		if (self.model.screen_index == splash_index):
			self.screen.blit(self.scaled_splash_image, self.splash_location)
		# Draw player entry screen
		elif (self.model.screen_index == player_screen_index):
			# Draw input information boxes
			i = 0
			while (i < self.num_funct_keys):
				# Only draw if key is used
				if (self.funct_keys_boxes[i].text != ""):
					pygame.draw.rect(self.screen, self.white, self.funct_keys_boxes[i].text_box, 1)
					# Draw text1
					self.txt_surface = self.block_title_font.render(self.funct_keys_boxes[i].text, True, self.white)  # Render text
					self.screen.blit(self.txt_surface, (self.funct_keys_boxes[i].x + 30, self.funct_keys_boxes[i].y + 5))  # Position text
					# Draw text2
					self.txt_surface = self.block_title_font.render(self.funct_keys_boxes[i].text2, True, self.white)  # Render text
					self.screen.blit(self.txt_surface, (self.funct_keys_boxes[i].x + 5, self.funct_keys_boxes[i].y + 25))  # Position text
					# Draw text2
					self.txt_surface = self.block_title_font.render(self.funct_keys_boxes[i].text3, True, self.white)  # Render text
					self.screen.blit(self.txt_surface, (self.funct_keys_boxes[i].x + 5, self.funct_keys_boxes[i].y + 40))  # Position text
				i += 1
			# Draw edit title
			self.txt_surface = self.edit_title_font.render(self.edit_title_text, True, self.white)  # Render text
			self.screen.blit(self.txt_surface, (self.screen_w/2 - self.screen_w/6, 15))  # Position text
			# Draw red/green team blocks
			pygame.draw.rect(self.screen, self.red, self.red_block)
			pygame.draw.rect(self.screen, self.green, self.green_block)
			# Draw block titles
			pygame.draw.rect(self.screen, self.white, self.red_block_title_box, 1)
			self.txt_surface = self.block_title_font.render(self.red_block_title, True, self.white)  # Render text
			self.screen.blit(self.txt_surface, (self.red_block_title_x + 50, self.red_block_title_y + 5))  # Position text
			pygame.draw.rect(self.screen, self.white, self.green_block_title_box, 1)
			self.txt_surface = self.block_title_font.render(self.green_block_title, True, self.white)  # Render text
			self.screen.blit(self.txt_surface, (self.green_block_title_x + 40, self.green_block_title_y + 5))  # Position text
			# Draw id/code name boxes
			i = 0
			while (i < self.num_boxes):
				pygame.draw.rect(self.screen, self.white, self.red_id_boxes[i].text_box)
				pygame.draw.rect(self.screen, self.white, self.red_code_name_boxes[i].text_box)
				pygame.draw.rect(self.screen, self.white, self.green_id_boxes[i].text_box)
				pygame.draw.rect(self.screen, self.white, self.green_code_name_boxes[i].text_box)
				# Display red ids
				self.txt_surface = self.font.render(self.red_id_boxes[i].text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.red_id_boxes[i].x + 5, self.red_id_boxes[i].y + 5))  # Position text
				# Display red code_names
				self.txt_surface = self.font.render(self.red_code_name_boxes[i].text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.red_code_name_boxes[i].x + 5, self.red_code_name_boxes[i].y + 5))  # Position text
				# Display green ids
				self.txt_surface = self.font.render(self.green_id_boxes[i].text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.green_id_boxes[i].x + 5, self.green_id_boxes[i].y + 5))  # Position text
				# Display green code_names
				self.txt_surface = self.font.render(self.green_code_name_boxes[i].text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.green_code_name_boxes[i].x + 5, self.green_code_name_boxes[i].y + 5))  # Position text
				i += 1
			# Draw popup box if needed
			if (self.network_popup_box.popup):
				pygame.draw.rect(self.screen, self.white, self.network_popup_box.text_box)
				self.txt_surface = self.popup_font.render(self.network_popup_box.text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_box_x + 10, self.popup_box_y + 20))  # Position text
				pygame.draw.rect(self.screen, self.black, self.network_popup_box.input_box, 1)
				self.txt_surface = self.popup_font.render(self.network_popup_box.input_feedback, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_input_x + 10, self.popup_input_y + 10))  # Position text
			# Draw id popup box
			elif (self.id_popup_box.popup):
				pygame.draw.rect(self.screen, self.white, self.id_popup_box.text_box)
				self.txt_surface = self.popup_font.render(self.id_popup_box.text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_box_x + 10, self.popup_box_y + 20))  # Position text
				pygame.draw.rect(self.screen, self.black, self.id_popup_box.input_box, 1)
				self.txt_surface = self.popup_font.render(self.id_popup_box.input_feedback, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_input_x + 10, self.popup_input_y + 10))  # Position text
			# Draw code name popup box if needed
			elif (self.id_popup_box.popup == False) and (self.code_name_popup_box.popup):
				pygame.draw.rect(self.screen, self.white, self.code_name_popup_box.text_box)
				self.txt_surface = self.popup_font.render(self.code_name_popup_box.text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_box_x + 10, self.popup_box_y + 20))  # Position text
				pygame.draw.rect(self.screen, self.black, self.code_name_popup_box.input_box, 1)
				self.txt_surface = self.popup_font.render(self.code_name_popup_box.input_feedback, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_input_x + 10, self.popup_input_y + 10))  # Position text
			# Draw equpiment id popup box
			elif (self.id_popup_box.popup == False) and (self.code_name_popup_box.popup == False) and (self.equip_id_popup_box.popup):
				pygame.draw.rect(self.screen, self.white, self.equip_id_popup_box.text_box)
				self.txt_surface = self.popup_font.render(self.equip_id_popup_box.text, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_box_x + 10, self.popup_box_y + 20))  # Position text
				pygame.draw.rect(self.screen, self.black, self.equip_id_popup_box.input_box, 1)
				self.txt_surface = self.popup_font.render(self.equip_id_popup_box.input_feedback, True, self.black)  # Render text
				self.screen.blit(self.txt_surface, (self.popup_input_x + 10, self.popup_input_y + 10))  # Position text
		# Draw game screen
		elif (self.model.screen_index == game_screen_index):
#			
			{}
		pygame.display.flip() # Puts images on screen

class Controller():
	def __init__(self, model, view):
		self.model = model
		self.view = view
		self.keep_going = True
		
	def update(self):

		if (self.model.screen_index == splash_index):
			{}
		elif (self.model.screen_index == player_screen_index):
			for event in pygame.event.get():
				if event.type == QUIT:
					self.keep_going = False
				# elif event.type == pygame.MOUSEBUTTONUP:
					# position = pygame.mouse.get_pos()

				elif event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						self.keep_going = False
					elif (event.key == K_LSHIFT) or (event.key == K_RSHIFT):
						self.shift = True
				elif event.type == pygame.KEYUP: #self is keyReleased!
					if (event.key == K_LSHIFT) or (event.key == K_RSHIFT):
						self.shift = False
					# Add player if key is F1 and if model needs a player id (prevents starting another player adding procedure) and network popup is not on screen
					if (event.key == K_F1) and (self.model.need_id == True) and (self.view.network_popup_box.popup == False):
						self.view.id_popup_box.popup = True
						self.model.need_id = False
					# Start game if F5 is pressed
					elif event.key == K_F5:
						self.model.start_game()
					# Prompt for new network ip if F6 is pressed and no other popups are on screen
					elif (event.key == K_F6) and (self.view.network_popup_box.popup == False) and (self.view.id_popup_box.popup == False) and (self.view.code_name_popup_box.popup == False) and ((self.view.equip_id_popup_box.popup == False)):
						self.view.network_popup_box.popup = True
					# Reset network ip to default (127.0.0.1) if F6 is pressed and network popup is not on screen
					elif (event.key == K_F7) and (self.view.network_popup_box.popup == False):
						self.model.change_network(default_network)
					# Clear players from tables if F12 is pressed
					elif event.key == K_F12:
						self.model.clear_players()
					# Enter characters into network popup
					elif (self.view.network_popup_box.popup):
						if (event.key == K_BACKSPACE):
							self.view.network_popup_box.input_feedback = self.view.network_popup_box.input_feedback[:-1]
						elif (event.key == K_RETURN):
							# Prevent empty input
							if (self.view.network_popup_box.input_feedback == ""):
								{}
							else:
								# remove popup
								self.view.network_popup_box.popup = False
								# Change network_ip
								self.model.change_network(str(self.view.network_popup_box.input_feedback))
								# clear feedback
								self.view.network_popup_box.input_feedback = ""
						else:
							self.view.network_popup_box.input_feedback += pygame.key.name(event.key)
					# Enter characters into id popup
					elif (self.view.id_popup_box.popup):
						if (event.key == K_BACKSPACE):
							self.view.id_popup_box.input_feedback = self.view.id_popup_box.input_feedback[:-1]
						elif (event.key == K_RETURN):
							# Keep game from crashing due to no input
							if (self.view.id_popup_box.input_feedback == ""):
								{}
							else:
								# Remove popup
								self.view.id_popup_box.popup = False
								# Check if id is in database
								self.model.check_id(int(self.view.id_popup_box.input_feedback))
								# clear feedback
								self.view.id_popup_box.input_feedback = ""
								# Receive codename from user if not in database
								self.view.code_name_popup_box.popup = self.model.need_code_name
								# Receive equipment id from user if code name already exists
								if (self.view.code_name_popup_box.popup == False):
									self.view.equip_id_popup_box.popup = True
						# prevent characters other than 0 to 9
						elif (event.key != K_0) and (event.key != K_1) and (event.key != K_2) and (event.key != K_3) and (event.key != K_4) and (event.key != K_5) and (event.key != K_6) and (event.key != K_7) and (event.key != K_8) and (event.key != K_9):
							{}
						else:
							self.view.id_popup_box.input_feedback += pygame.key.name(event.key)
					# Enter characters into code name popup
					elif (self.view.code_name_popup_box.popup):
						if (event.key == K_BACKSPACE):
							self.view.code_name_popup_box.input_feedback = self.view.code_name_popup_box.input_feedback[:-1]
						elif (event.key == K_RETURN):
							# Prevent empty code names
							if (self.view.code_name_popup_box.input_feedback == ""):
								{}
							else:
								# remove popup
								self.view.code_name_popup_box.popup = False
								# Enter code name into database
								self.model.enter_code_name(str(self.view.code_name_popup_box.input_feedback))
								# clear feedback
								self.view.code_name_popup_box.input_feedback = ""
								# Receive equipment id from user
								self.view.equip_id_popup_box.popup = True
						# Prevent key's name from being input into popup
						elif (event.key == K_LSHIFT) or (event.key == K_RSHIFT):
							{}
						else:
							# Input lowercase letters
							if (self.shift == False):
								self.view.code_name_popup_box.input_feedback += pygame.key.name(event.key)
							# Input uppercase letters
							else:
								char = pygame.key.name(event.key)
								self.view.code_name_popup_box.input_feedback += char.capitalize()
					# Enter characters into equipment id popup
					elif (self.view.equip_id_popup_box.popup):
						if (event.key == K_BACKSPACE):
							self.view.equip_id_popup_box.input_feedback = self.view.equip_id_popup_box.input_feedback[:-1]
						elif (event.key == K_RETURN):
							# Keep game from crashing due to no input
							if (self.view.equip_id_popup_box.input_feedback == ""):
								{}
							else:
								self.view.equip_id_popup_box.popup = False
								# Enter player into game
								self.model.add_player(int(self.view.equip_id_popup_box.input_feedback))
								# Clear feedback
								self.view.equip_id_popup_box.input_feedback = ""
								# Remove popup
								self.view.equip_id_popup_box.popup = False
								# Allow new player to be entered
								self.model.need_id = True
						# prevent characters other than 0 to 9
						elif (event.key != K_0) and (event.key != K_1) and (event.key != K_2) and (event.key != K_3) and (event.key != K_4) and (event.key != K_5) and (event.key != K_6) and (event.key != K_7) and (event.key != K_8) and (event.key != K_9):
							{}
						else:
							self.view.equip_id_popup_box.input_feedback += pygame.key.name(event.key)
			keys = pygame.key.get_pressed()

# # Database code
# import psycopg2
# from psycopg2 import sql
# # Define connection parameters
# connection_params = {
#     'dbname': 'photon',
#     'user': 'student',
#     #'password': 'student',
#     #'host': 'localhost',
#     #'port': '5432'
# }

# try:
# 	# Connect to PostgreSQL
#     conn = psycopg2.connect(**connection_params)
#     cursor = conn.cursor()

#     # Execute a query
#     cursor.execute("SELECT version();")

#     # Fetch and display the result
#     version = cursor.fetchone()
#     print(f"Connected to - {version}")

#     # Insert two players
#     cursor.execute('''
#         INSERT INTO players (id, codename)
#         VALUES (%s, %s);
#     ''', ('1', 'Shark'))
	
# 	# cursor.execute('''
# 	# 	INSERT INTO players (id, codename)
# 	# 	VALUES (%s, %s);
# 	# ''', ('2', 'Lazer'))

#     # Commit the changes
#     conn.commit()

#     # Fetch and display data from the table
#     cursor.execute("SELECT * FROM players;")
#     rows = cursor.fetchall()
#     for row in rows:
#         print(row)

# except Exception as error:
#     print(f"Error connecting to PostgreSQL database: {error}")

# finally:
#     # Close the cursor and connection
#     if cursor:
#         cursor.close()
#     if conn:
#         conn.close()

# Running the code code
pygame.init()
m = Model()
v = View(m)
c = Controller(m, v)
while c.keep_going:
	c.update()
	m.update()
	v.update()

	sleep(sleep_time)
m.conn.close()
m.cursor.close()



