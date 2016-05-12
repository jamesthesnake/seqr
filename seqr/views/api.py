from django.contrib.auth.decorators import login_required
from xbrowse_server.server_utils import HttpResponse
from xbrowse_server.base.models import Project, Family
from django.db import connection
from django.core.serializers.json import DateTimeAwareJSONEncoder
import json



@login_required
def user(request):
    """Returns user information"""
    json_obj = {key: value for key, value in request.user._wrapped.__dict__.items()
                if not key.startswith("_") and key != "password"}
    json_response_string = json.dumps({"user": json_obj}, sort_keys=True, indent=4, default=DateTimeAwareJSONEncoder().default)

    return HttpResponse(json_response_string, content_type="application/json")


@login_required
def projects(request):
    """Returns information on all projects this user has access to"""

    # look up all projects the user has permissions to view
    if request.user.is_staff:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(projectcollaborator__user=request.user)

    for project in projects:
        if not project.can_view(request.user):
            raise ValueError  # TODO error handling

    # serialize to json
    json_obj = {"projects": list(projects.values())}
    json_response_string = json.dumps(json_obj, sort_keys=True, indent=4, default=DateTimeAwareJSONEncoder().default)

    return HttpResponse(json_response_string, content_type="application/json")


@login_required
def projects_with_stats(request):
    """TODO docs"""

    # TODO check permissions

    #for project in projects:
    #    if not project.can_view(request.user):
    #        raise ValueError  # TODO error handling

    # use raw SQL to compute family and individual counts using nested queries
    cursor = connection.cursor()
    cursor.execute("""
      SELECT
        *,
        (SELECT count(*) FROM base_family WHERE project_id=base_project.id) AS num_families,
        (SELECT count(*) FROM base_individual WHERE project_id=base_project.id) AS num_individuals
      FROM base_project
    """)

    columns = [col[0] for col in cursor.description]
    json_obj = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    json_response_string = json.dumps(
            {"projects": json_obj}, sort_keys=True, indent=4, default=DateTimeAwareJSONEncoder().default)

    return HttpResponse(json_response_string, content_type="application/json")

