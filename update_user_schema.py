from app import app, db
from models import User
from sqlalchemy import text

def update_user_schema():
    with app.app_context():
        # Check if the two_factor_enabled column exists
        result = db.session.execute(text("PRAGMA table_info(user)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add missing columns if they don't exist
        if 'two_factor_enabled' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0"))
            print("Added two_factor_enabled column")
        
        if 'two_factor_secret' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN two_factor_secret VARCHAR(32)"))
            print("Added two_factor_secret column")
        
        if 'backup_codes' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN backup_codes TEXT"))
            print("Added backup_codes column")
        
        if 'sms_login_enabled' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN sms_login_enabled BOOLEAN DEFAULT 0"))
            print("Added sms_login_enabled column")
        
        if 'failed_login_attempts' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
            print("Added failed_login_attempts column")
        
        if 'account_locked_until' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN account_locked_until DATETIME"))
            print("Added account_locked_until column")
        
        if 'last_password_change' not in columns:
            db.session.execute(text("ALTER TABLE user ADD COLUMN last_password_change DATETIME"))
            print("Added last_password_change column")
        
        # Update existing users to set default values for the new columns
        db.session.execute(text("""
            UPDATE user SET 
                last_password_change = datetime('now')
            WHERE last_password_change IS NULL
        """))
        
        db.session.commit()
        print("Database schema updated successfully!")

if __name__ == '__main__':
    update_user_schema()