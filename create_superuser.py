import os
import django

# django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User

#admin info
USERNAME = 'admin'
PASSWORD = 'admin1234'  

def create_admin():
    try:
        if not User.objects.filter(username=USERNAME).exists():
            print(f"Creating superuser: {USERNAME}...")
            User.objects.create_superuser(USERNAME, 'admin@example.com', PASSWORD)
            print(" Superuser created successfully!")
        else:
            print(" Superuser already exists. Skipping.")
    except Exception as e:
        print(f" Error creating superuser: {e}")

if __name__ == "__main__":
    create_admin()