from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from PIL import Image
import io
import random
import numpy as np
import cv2
import pyautogui
from pynput import keyboard, mouse
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

class RobloxAgent:
    def __init__(self):
        self.driver = None
        self.wait_time = 10
        load_dotenv()
        self.setup_logging()
        self.current_step = ""
        self.screenshots_dir = "monitoring"
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        
        # Initialize input controllers
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        
        # Game state tracking
        self.is_in_game = False
        self.player_position = None
        self.current_health = 100
        self.current_energy = 100
        
        # Accessibility settings
        self.input_delay = 0.1  # Adjustable delay between inputs
        self.movement_sensitivity = 1.0  # Mouse movement sensitivity multiplier
        self.auto_heal_threshold = 50  # Health percentage to trigger auto-healing

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('agent.log'),
                logging.StreamHandler()
            ]
        )

    def take_screenshot(self, step_name):
        """Capture and save a screenshot of the current browser window"""
        if self.driver:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.screenshots_dir}/{step_name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            logging.info(f"Screenshot saved: {filename}")
            return filename
        return None

    def update_status(self, step, details=""):
        """Update the current step and log the status"""
        self.current_step = step
        message = f"Current Step: {step}"
        if details:
            message += f" - {details}"
        logging.info(message)

    def setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, self.wait_time)

    def login(self, username=None, password=None):
        """Login to Roblox account"""
        try:
            # Use environment variables if credentials not provided
            username = username or os.getenv('ROBLOX_USERNAME')
            password = password or os.getenv('ROBLOX_PASSWORD')

            if not username or not password:
                raise ValueError("Roblox credentials not provided")

            self.update_status("Navigating to login page")
            self.driver.get('https://www.roblox.com/login')
            self.take_screenshot("login_page")

            # Wait for and fill in the login form
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
            password_field = self.driver.find_element(By.ID, 'login-password')

            self.update_status("Entering credentials")
            # Simulate human-like typing for username
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))  # Random delay between keystrokes
            
            time.sleep(random.uniform(0.5, 1.5))  # Natural pause before typing password
            
            # Simulate human-like typing for password
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))  # Random delay between keystrokes
                
            time.sleep(random.uniform(0.8, 1.2))  # Natural pause after typing
            self.take_screenshot("credentials_entered")

            # Handle cookie banner if present
            try:
                cookie_banner = self.driver.find_element(By.CLASS_NAME, "cookie-banner-bg")
                if cookie_banner.is_displayed():
                    accept_button = self.driver.find_element(By.CLASS_NAME, "btn-cookie-banner-ok")
                    accept_button.click()
                    time.sleep(1)  # Wait for banner to disappear
            except Exception:
                pass  # Cookie banner not present

            self.update_status("Clicking login button")
            login_button = self.driver.find_element(By.ID, "login-button")
            login_button.click()
            self.take_screenshot("login_clicked")

            # Wait for login to complete
            time.sleep(5)  # Allow time for login and potential redirects

            return True

        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def launch_blox_fruits(self):
        """Navigate to and launch Blox Fruits"""
        try:
            self.update_status("Navigating to Blox Fruits page")
            self.driver.get('https://www.roblox.com/games/2753915549')
            self.take_screenshot("blox_fruits_page")

            # Wait for and click the Play button
            play_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'play-button-container')))
            play_button.click()
            self.take_screenshot("game_launched")

            print("Launching Blox Fruits...")
            return True

        except Exception as e:
            print(f"Failed to launch Blox Fruits: {str(e)}")
            return False

    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.update_status("Closing browser")
            self.driver.quit()
            logging.info("Browser session ended")

    def get_current_status(self):
        """Return the current status of the agent"""
        return {
            "current_step": self.current_step,
            "browser_active": self.driver is not None,
            "in_game": self.is_in_game,
            "player_position": self.player_position,
            "health": self.current_health,
            "energy": self.current_energy
        }
        
    def capture_game_screen(self):
        """Capture and process the game screen for analysis"""
        screenshot = self.take_screenshot("game_state")
        if screenshot:
            image = cv2.imread(screenshot)
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return None

    def detect_player_position(self, screen_image):
        """Detect player position from the game screen"""
        try:
            # Convert image to HSV color space for better color detection
            hsv = cv2.cvtColor(screen_image, cv2.COLOR_RGB2HSV)
            
            # Define color range for player character (adjust these values based on character appearance)
            lower_bound = np.array([0, 0, 200])  # Example values
            upper_bound = np.array([180, 30, 255])
            
            # Create mask and find contours
            mask = cv2.inRange(hsv, lower_bound, upper_bound)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find the largest contour (assumed to be the player)
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    self.player_position = (cx, cy)
                    return True
            return False
        except Exception as e:
            logging.error(f"Error detecting player position: {str(e)}")
            return False

    def simulate_movement(self, direction, duration=0.5):
        """Simulate player movement in specified direction"""
        key_mapping = {
            'forward': 'w',
            'backward': 's',
            'left': 'a',
            'right': 'd',
            'jump': Key.space
        }
        
        if direction in key_mapping:
            key = key_mapping[direction]
            try:
                self.keyboard.press(key)
                time.sleep(duration * self.input_delay)
                self.keyboard.release(key)
                return True
            except Exception as e:
                logging.error(f"Error simulating movement: {str(e)}")
                return False
        return False

    def simulate_combat(self, action):
        """Simulate combat actions"""
        try:
            if action == 'basic_attack':
                self.mouse.click(Button.left)
            elif action == 'special_attack':
                self.keyboard.press('f')
                time.sleep(0.2)
                self.keyboard.release('f')
            elif action == 'dodge':
                self.keyboard.press(Key.shift)
                self.simulate_movement('right', 0.3)
                self.keyboard.release(Key.shift)
            return True
        except Exception as e:
            logging.error(f"Error simulating combat: {str(e)}")
            return False

    def update_game_state(self):
        """Update the current game state including health and energy levels"""
        screen = self.capture_game_screen()
        if screen is not None:
            self.detect_player_position(screen)
            # Add health and energy detection logic here
            # This would involve analyzing specific screen regions where these values are displayed
            
            # Example placeholder logic:
            if self.current_health < self.auto_heal_threshold:
                self.simulate_combat('heal')

    def set_accessibility_settings(self, input_delay=None, movement_sensitivity=None, auto_heal_threshold=None):
        """Update accessibility settings for the game controls"""
        if input_delay is not None:
            self.input_delay = max(0.1, min(2.0, input_delay))  # Clamp between 0.1 and 2.0 seconds
        if movement_sensitivity is not None:
            self.movement_sensitivity = max(0.1, min(2.0, movement_sensitivity))  # Clamp between 0.1 and 2.0
        if auto_heal_threshold is not None:
            self.auto_heal_threshold = max(0, min(100, auto_heal_threshold))  # Clamp between 0 and 100 percent

def main():
    agent = RobloxAgent()
    try:
        agent.setup_driver()
        if agent.login():
            print("Successfully logged in!")
            agent.launch_blox_fruits()
        else:
            print("Failed to log in")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        agent.close()

if __name__ == '__main__':
    main()