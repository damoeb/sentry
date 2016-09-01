from __future__ import absolute_import

import six

from rest_framework.response import Response

from sentry.app import search
from .project_group_index import build_query_params_from_request, ValidationError
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.api.serializers import serialize
from sentry.api.serializers.models.group import StreamGroupSerializer
from sentry.models import Project


class OrganizationIssuesSearchEndpoint(OrganizationEndpoint):

    def get(self, request, organization):
        team_list = list(request.access.teams)
        projects = Project.objects.filter(
            team__in=team_list,
        )

        try:
            query_kwargs = build_query_params_from_request(request, projects)
        except ValidationError as exc:
            return Response({'detail': six.text_type(exc)}, status=400)

        cursor_result = search.query(**query_kwargs)

        results = list(cursor_result)

        context = serialize(
            results, request.user, StreamGroupSerializer(
                stats_period=None
            )
        )

        response = Response(context)
        response['Link'] = ', '.join([
            self.build_cursor_link(request, 'previous', cursor_result.prev),
            self.build_cursor_link(request, 'next', cursor_result.next),
        ])

        return response
