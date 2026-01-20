"""add_christian_book_fields

Add author, category, and scripture_focus fields to books table.
These fields support the Christian/Biblical book categorization.

Revision ID: add_christian_fields
Revises: 6d3b5339a145
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_christian_fields'
down_revision: Union[str, Sequence[str], None] = '6d3b5339a145'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Christian-specific fields to books table."""
    
    # Create the BookCategory enum type
    bookcategory_enum = sa.Enum(
        'BIBLICAL_STUDIES',
        'THEOLOGY',
        'DEVOTIONAL',
        'CHRISTIAN_LIVING',
        'PRAYER_WORSHIP',
        'CHURCH_HISTORY',
        'APOLOGETICS',
        'FAMILY_MARRIAGE',
        'YOUTH_CHILDREN',
        'MISSIONS_EVANGELISM',
        'SPIRITUAL_GROWTH',
        'BIOGRAPHY_TESTIMONY',
        'COMMENTARY',
        'REFERENCE',
        'OTHER',
        name='bookcategory'
    )
    bookcategory_enum.create(op.get_bind(), checkfirst=True)
    
    # Add author column
    op.add_column(
        'books',
        sa.Column('author', sa.String(length=255), nullable=True)
    )
    
    # Add category column with default value
    op.add_column(
        'books',
        sa.Column(
            'category',
            sa.Enum(
                'BIBLICAL_STUDIES',
                'THEOLOGY',
                'DEVOTIONAL',
                'CHRISTIAN_LIVING',
                'PRAYER_WORSHIP',
                'CHURCH_HISTORY',
                'APOLOGETICS',
                'FAMILY_MARRIAGE',
                'YOUTH_CHILDREN',
                'MISSIONS_EVANGELISM',
                'SPIRITUAL_GROWTH',
                'BIOGRAPHY_TESTIMONY',
                'COMMENTARY',
                'REFERENCE',
                'OTHER',
                name='bookcategory'
            ),
            nullable=False,
            server_default='OTHER'
        )
    )
    
    # Add scripture_focus column
    op.add_column(
        'books',
        sa.Column('scripture_focus', sa.String(length=255), nullable=True)
    )
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_books_author'), 'books', ['author'], unique=False)
    op.create_index(op.f('ix_books_category'), 'books', ['category'], unique=False)
    op.create_index(op.f('ix_books_is_featured'), 'books', ['is_featured'], unique=False)
    op.create_index(op.f('ix_books_is_published'), 'books', ['is_published'], unique=False)


def downgrade() -> None:
    """Remove Christian-specific fields from books table."""
    
    # Drop indexes
    op.drop_index(op.f('ix_books_is_published'), table_name='books')
    op.drop_index(op.f('ix_books_is_featured'), table_name='books')
    op.drop_index(op.f('ix_books_category'), table_name='books')
    op.drop_index(op.f('ix_books_author'), table_name='books')
    
    # Drop columns
    op.drop_column('books', 'scripture_focus')
    op.drop_column('books', 'category')
    op.drop_column('books', 'author')
    
    # Drop the enum type
    sa.Enum(name='bookcategory').drop(op.get_bind(), checkfirst=True)
