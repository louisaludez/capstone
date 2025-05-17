from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from faker import Faker
import random
import time

# Initialize Faker for generating random names
fake = Faker()

# Filipino names data
filipino_first_names = [
    "Angelo", "Maria", "Juan", "Jose", "Miguel", "Gabriel", "Rafael", "Antonio",
    "Francisco", "Carlos", "Luis", "Manuel", "Ricardo", "Eduardo", "Roberto",
    "Fernando", "Pedro", "Enrique", "Alberto", "Victor", "Rosa", "Ana", "Sofia",
    "Isabella", "Clara", "Elena", "Carmen", "Beatriz", "Diana", "Gloria",
    "John", "Mark", "Michael", "Christian", "Paolo", "Marco", "Daniel", "David",
    "Andrea", "Angela", "Michelle", "Patricia", "Christine", "Jennifer", "Mary",
    "Jasmine", "Nicole", "Sarah", "Kathleen", "Joyce", "Marvin", "Ryan",
    "Joshua", "Justin", "Adrian", "Bryan", "Carlo", "Patrick", "Jerome"
]

filipino_surnames = [
    "Santos", "Reyes", "Cruz", "Garcia", "Mendoza", "Torres", "Ramos", "Flores",
    "De la Cruz", "Gonzales", "Bautista", "Rodriguez", "Fernandez", "Lopez",
    "Perez", "Martinez", "Rivera", "Aquino", "Castillo", "Sanchez", "Ramirez",
    "Morales", "Del Rosario", "Castro", "Gonzaga", "Villegas", "Tan", "Delos Santos",
    "Domingo", "Dizon", "Vasquez", "Cortez", "Gutierrez", "Navarro", "Estrada",
    "De Guzman", "Salvador", "Mercado", "De Leon", "Villanueva", "Aguilar", "Robles",
    "De Vera", "Ruiz", "Pascual", "Sison", "Marquez", "Valencia", "Soriano",
    "Santiago", "Miranda", "Ocampo", "Romero", "Lacson", "Padilla", "Diaz"
]

def generate_filipino_email():
    """Generate a random email with Filipino names"""
    first_name = random.choice(filipino_first_names)
    surname = random.choice(filipino_surnames)
    
    # Only add number with 1/15 chance
    should_add_number = random.randint(1, 10) == 1
    random_num = random.randint(1, 999) if should_add_number else ""
    
    # Different email formats, with and without dots
    email_formats = [
        # No dot formats (more common)
        f"{first_name.lower()}{surname.lower()}{random_num}@gmail.com",
        f"{surname.lower()}{first_name.lower()}{random_num}@gmail.com",
        f"{first_name[0].lower()}{surname.lower()}{random_num}@gmail.com",
        f"{first_name.lower()}{surname[0].lower()}{random_num}@gmail.com",
        f"{surname.lower()}{first_name[0].lower()}{random_num}@gmail.com",
    ]
    
    # Add dot formats with 1/5 chance
    if random.randint(1, 4) == 1:
        dot_formats = [
            f"{first_name.lower()}.{surname.lower()}{random_num}@gmail.com",
            f"{surname.lower()}.{first_name.lower()}{random_num}@gmail.com",
        ]
        email_formats.extend(dot_formats)
    
    return random.choice(email_formats)

def get_random_response():
    """Generate a random response favoring 3-5 with small chance of 1-2"""
    random_num = random.random()
    if random_num < 0.05:  # 5% chance for 1
        return 1
    elif random_num < 0.10:  # 5% chance for 2
        return 2
    elif random_num < 0.20:  # 10% chance for 3
        return 3
    
    else:  # 80% chance for values 3-5
        return random.randint(4, 5)

def fill_form(driver):
    try:
        # Wait for email field and fill it
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_field.send_keys(generate_filipino_email())

        # Find all radio button groups (each question)
        sections = ["Awareness", "Compliance", "Ethical"]
        
        # For each section, find the radio buttons and select random options
        for section in sections:
            questions = driver.find_elements(By.CSS_SELECTOR, "div[role='radiogroup']")
            for question in questions:
                # Find all radio buttons in the question
                options = question.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                # Select a random option (index 0-4 for responses 1-5)
                random_choice = get_random_response()
                options[random_choice - 1].click()
                time.sleep(0.5)  # Small delay to prevent detection

        # Submit the form
        submit_button = driver.find_element(By.CSS_SELECTOR, "div[role='button'][jsname='M2UYVd']")
        submit_button.click()

        # Wait for submission confirmation
        time.sleep(2)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

    return True

def main():
    # Setup Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # Uncomment to run in headless mode
    
    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Google Form URL
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeLxpYvi6BNMhrTo1P486iqwboMzR-W5PtBAQKR_kg1bMsq9g/viewform?usp=header"
    
    # Number of submissions
    num_submissions = 13

    try:
        for i in range(num_submissions):
            print(f"Filling form submission {i + 1}/{num_submissions}")
            driver.get(form_url)
            
            if fill_form(driver):
                print(f"Successfully submitted form {i + 1}")
            else:
                print(f"Failed to submit form {i + 1}")
            
            time.sleep(2)  # Wait between submissions

    except Exception as e:
        print(f"An error occurred in main execution: {str(e)}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main() 