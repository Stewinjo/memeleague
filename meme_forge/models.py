from django.db import models
from core.dataclasses import TemplateTags

class MemeTemplate(models.Model):
    """
    Model for storing meme templates.
    """
    # A unique, user-friendly name for the meme template
    name = models.CharField(max_length=150, unique=True)  # Increased length to allow more descriptive names
    alternative_names = models.JSONField(default=list, blank=True)  # Allow blank (empty list) for optional field

    # URLs for image storage and fallback
    image_url_local = models.CharField(max_length=255, blank=True)  # Use CharField for flexibility with local paths
    image_url_web = models.URLField(blank=True)  # Allow blank for cases where the web URL might be missing

    # File properties
    format = models.CharField(
        max_length=10,
        choices=[('jpg', 'JPG'), ('png', 'PNG'), ('gif', 'GIF')],
        default='jpg'
    )  # Add choices for known formats
    file_size = models.CharField(max_length=15, default="0 KB")  # Allow reasonable defaults

    # Tags and text box metadata
    tags = models.JSONField(default=list, blank=True)  # Default to an empty list
    text_boxes = models.JSONField(default=list, blank=True)  # Default to an empty list

    # Image dimensions
    width = models.PositiveIntegerField(default=0)  # Ensure positive integer values
    height = models.PositiveIntegerField(default=0)  # Ensure positive integer values

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Add an index for the 'name' field to optimize queries
        ]

    def __str__(self):
        return self.name

    @property
    def dimensions(self):
        """
        Compute the dimensions as a string in the format 'width x height'.
        """
        return f"{self.width}x{self.height}"

    @staticmethod
    def validate_tags(tags):
        """
        Validate the provided tags against a set of predefined tags.
        """
        valid_tags = {tag.value for tag in TemplateTags}
        if not all(tag in valid_tags for tag in tags):
            raise ValueError(f"Invalid tags. Valid options are: {valid_tags}")

    def clean(self):
        """
        Additional validations for fields to ensure consistency.
        """
        if self.width > 10000 or self.height > 10000:
            raise ValueError("Width and height values are too large, must be under 10,000.")
        if not self.file_size.endswith("KB") and not self.file_size.endswith("MB"):
            raise ValueError("File size must be a string ending with 'KB' or 'MB'.")
