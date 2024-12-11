import os
import json
from django.core.management.base import BaseCommand
from meme_forge.models import MemeTemplate


class Command(BaseCommand):
    help = "Populates the database with meme templates from JSON files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='meme_forge/data/meme_templates',
            help="Directory containing JSON files for meme templates"
        )
        parser.add_argument(
            '--image-dir',
            type=str,
            default='static/images/memes_raw',
            help="Directory where meme images are stored"
        )

    def handle(self, *args, **kwargs):
        data_dir = kwargs['data_dir']
        image_dir = kwargs['image_dir']

        if not os.path.exists(data_dir):
            self.stderr.write(self.style.ERROR(f"Data directory not found: {data_dir}"))
            return

        if not os.path.exists(image_dir):
            self.stderr.write(self.style.ERROR(f"Image directory not found: {image_dir}"))
            return

        for json_file in os.listdir(data_dir):
            if not json_file.endswith('.json'):
                continue

            json_path = os.path.join(data_dir, json_file)
            try:
                with open(json_path, 'r') as file:
                    template_data = json.load(file)

                # Extract fields from JSON
                name = template_data.get('title')
                alternative_names = template_data.get('alternative_names', "").split(", ")
                image_url_web = template_data.get('template_url')
                file_format = template_data.get('format')
                dimensions = template_data.get('dimensions', "0x0 px")  # Default to "0x0 px" if missing
                file_size = template_data.get('file_size', "0 KB")  # Default to "0 KB" if missing

                if not all([name, image_url_web, file_format, dimensions, file_size]):
                    self.stderr.write(self.style.WARNING(f"Skipping incomplete template: {json_file}"))
                    continue

                # Use the JSON file's name (without extension) to locate the corresponding image file
                image_filename = json_file.replace('.json', f".{file_format}")
                local_image_path = os.path.join(image_dir, image_filename)
                if not os.path.exists(local_image_path):
                    self.stderr.write(self.style.WARNING(f"Image file not found: {local_image_path}. Skipping template '{name}'."))
                    continue

                image_url_local = f"/static/images/memes_raw/{image_filename}"

                # Parse dimensions into width and height
                try:
                    width, height = map(int, dimensions.replace(" px", "").split("x"))
                except ValueError:
                    self.stderr.write(self.style.WARNING(f"Invalid dimensions format for '{name}': {dimensions}"))
                    width, height = 0, 0  # Default to 0x0 for invalid dimensions

                # Check if the template already exists
                if MemeTemplate.objects.filter(name=name).exists():
                    self.stdout.write(self.style.WARNING(f"Template '{name}' already exists. Skipping."))
                    continue

                # Save to the database
                MemeTemplate.objects.create(
                    name=name,
                    alternative_names=alternative_names,
                    image_url_web=image_url_web,
                    image_url_local=image_url_local,
                    format=file_format,
                    file_size=file_size,
                    width=width,
                    height=height,
                    tags=[],  # Add tags logic if applicable
                    text_boxes=[],  # Add text box logic if applicable
                )
                self.stdout.write(self.style.SUCCESS(f"Template '{name}' added successfully."))

            except json.JSONDecodeError:
                self.stderr.write(self.style.ERROR(f"Invalid JSON format in file: {json_file}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Unexpected error processing file {json_file}: {str(e)}"))
