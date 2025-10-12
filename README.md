# myspares-backend

a fully functional backend service for an e-commerce platform, providing secure authentication, admin management, and client-facing APIs. 

## Documentation

### [Authentication](backend/authentication/urls.py)
| Action     | Endpoint                           | Method | Required Fields                             |
| ---------- | ---------------------------------- | ------ | ------------------------------------------- |
| register   | `/api/auth/register/`              | `POST` | `username`, `phone_number`, `password`      |
| send OTP   | `/api/auth/register/send-otp/`     | `POST` | `username`, `phone_number`, `password`      |
| verify OTP | `/api/auth/register/verify-otp/`   | `POST` | `phone_number`, `otp`                       |
| login      | `/api/auth/login/`                 | `POST` | `phone_number`, `password`                  |
| refresh    | `/api/auth/refresh/`               | `POST` | `none [COOKIE: {refresh_token}]`            |
| logout     | `/api/auth/logout/`                | `POST` | `header: Authorization: Bearer <access_token>` `body: none [COOKIE: {refresh_token}]` |

### [Client](backend/client/urls.py)
| Action           | Endpoint                                          | Method   | Required Fields  |
| ---------------- | ------------------------------------------------- | -------- | ---------------- |
| list cart        | `/api/client/<user_id>/cart/`                     | `GET`    | `none`           |
| add product      | `/api/client/<user_id>/cart/add/<product_id>/`    | `POST`   | `none`           |
| remove product   | `/api/client/<user_id>/cart/remove/<product_id>/` | `DELETE` | `none`           |
| get address      | `/api/client/<user_id>/address/`                  | `GET`    | `none`           |
| update address   | `/api/client/<user_id>/address/update/`           | `PUT`    | *[address fields](backend/client/models.py#L171)* |

### [Utility](backend/utility/urls.py) [api/utils/]

### [Admin](backend/admin/urls.py) [api/admin/]


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

## Testing

*postman workspace: [MySpares Workspace](https://www.postman.com/waltermichelraja/myspares-workspace/overview)*