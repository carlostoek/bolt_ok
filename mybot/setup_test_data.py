import sys
sys.path.insert(0, '.')
from admin_panel.app import create_app
from admin_panel.extensions import db
from database.narrative_models import StoryFragment, NarrativeChoice
from database.models import ShopItem
from sqlalchemy import delete
import os

def setup_test_data():
    app = create_app('development')
    with app.app_context():
        # Clean up previous test data
        db.session.execute(delete(NarrativeChoice))
        db.session.execute(delete(StoryFragment))
        db.session.execute(delete(ShopItem))
        db.session.commit()

        # Create test data
        simple = StoryFragment(key='TEST_SIMPLE', text='Simple fragment', min_besitos=10)
        db.session.add(simple)

        product = ShopItem(name='Unlocker', price=50, unlocks_fragment_key='TEST_LOCKED')
        locked = StoryFragment(key='TEST_LOCKED', text='Locked fragment', required_role='vip')
        db.session.add(product)
        db.session.add(locked)
        
        with_choices = StoryFragment(key='TEST_WITH_CHOICES', text='Fragment with choices', min_besitos=20)
        db.session.add(with_choices)
        db.session.flush() # to get the id for with_choices
        choice1 = NarrativeChoice(source_fragment_id=with_choices.id, destination_fragment_key='TEST_SIMPLE', text='Go to simple')
        choice2 = NarrativeChoice(source_fragment_id=with_choices.id, destination_fragment_key='TEST_LOCKED', text='Go to locked')
        db.session.add_all([choice1, choice2])

        no_choices = StoryFragment(key='TEST_NO_CHOICES', text='Fragment with no choices')
        db.session.add(no_choices)

        db.session.commit()
    print("Test data created.")

def cleanup_test_data():
    app = create_app('development')
    with app.app_context():
        db.session.execute(delete(NarrativeChoice))
        db.session.execute(delete(StoryFragment))
        db.session.execute(delete(ShopItem))
        db.session.commit()
    print("Test data cleaned up.")

if __name__ == '__main__':
    setup_test_data()
