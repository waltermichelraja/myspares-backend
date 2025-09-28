# myspares-backend

a fully functional backend service for an e-commerce platform, providing secure authentication, admin management, and client-facing APIs. 

## Documentation

### [Authentication](backend/authentication/urls.py)
| Action    | Endpoint                | Method | Required Fields                             |
| --------- | ----------------------- | ------ | ------------------------------------------- |
| register  | `/api/auth/register/`   | `POST` | `username`, `phone_number`, `password`      |
| login     | `/api/auth/login/`      | `POST` | `phone_number`, `password`                  |
| refresh   | `/api/auth/refresh/`    | `POST` | `None [requires {refresh_token} in cookie]` |
| logout    | `/api/auth/logout/`     | `POST` | `None [requires {refresh_token} in cookie]` |

### [Client](backend/client/urls.py)
| Action           | Endpoint                                          | Method   | Required Fields  |
| ---------------- | ------------------------------------------------- | -------- | ---------------- |
| list card        | `/api/client/<user_id>/cart/`                     | `GET`    | `None`           |
| add product      | `/api/client/<user_id>/cart/add/<product_id>/`    | `POST`   | `None`           |
| remove product   | `/api/client/<user_id>/cart/remove/<product_id>/` | `DELETE` | `None`           |
| get address      | `/api/client/<user_id>/address/`                  | `GET`    | `None`           |
| update address   | `/api/client/<user_id>/address/update/`           | `PUT`    | `address fields` |



### [Admin](backend/admin/urls.py) [urls.py]


## Installation & Setup
```bash
# clone repository
git clone https://github.com/waltermichelraja/myspares-backend.git

# switch to the local-repo
cd myspares-backend

# switch branch
git switch -c backend

# setup DJANGO_KEY and MONGO_URI in .env [your project environment] 

# create virtual environment <env>
python3 -m venv env

# switch interpreter to env [linux/mac]
source env/bin/activate

# install packages through requirements.txt
pip install -r requirements.txt

# run django server
python manage.py runserver
```