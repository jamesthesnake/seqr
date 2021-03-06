from django.core.management.base import BaseCommand

from xbrowse_server.base.models import Project, VCFFile
from xbrowse_server import sample_management

import os
import yaml
from xbrowse.utils import slugify


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):

        project_id = args[0]
        project = Project.objects.get(project_id=project_id)
        project_dir = os.path.abspath(args[1])
        project_yaml_file = os.path.join(project_dir, 'project.yaml')

        project_spec = yaml.load(open(project_yaml_file))

        # load in sample IDs that we'll use for the project
        sample_id_file = os.path.join(project_dir, project_spec['sample_id_list'])
        sample_ids = [l.strip('\n') for l in open(sample_id_file)]
        sample_ids = [slugify(s, separator='_') for s in sample_ids]
        sample_management.add_indiv_ids_to_project(project, sample_ids)

        # set meta info
        project.project_name = project_spec['project_name']
        project.save()

        # nicknames
        if 'nicknames' in project_spec:
            # todo
            pass

        # load individuals
        if 'ped_files' in project_spec:
            for relative_path in project_spec['ped_files']:
                ped_file_path = os.path.join(project_dir, relative_path)
                sample_management.update_project_from_fam(project, open(ped_file_path))
                # todo: add awesome-slugify to above

        # set VCF files
        if 'vcf_files' in project_spec:
            for relative_path in project_spec['vcf_files']:
                vcf_file_path = os.path.join(project_dir, relative_path)
                # todo: this should be a fn somewhere that add_vcf_to_project uses too
                vcf_file = VCFFile.objects.get_or_create(file_path=vcf_file_path)[0]
                sample_management.add_vcf_file_to_project(project, vcf_file)
