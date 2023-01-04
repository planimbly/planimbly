from apps.organizations.models import Organization, Unit, Workplace
from planimbly.settings import VUE3_CDN, VUE2_CDN, ENV_STAGE, USE_HUEY


def organization_data(request):
    user = request.user
    if not user.is_anonymous:
        organization = Organization.objects.filter(id=user.user_org.id).first()
        unit_list = Unit.objects.filter(unit_org=organization)
        workplace_dict = {}
        for unit in unit_list:
            workplace_list = list(Workplace.objects.filter(workplace_unit=unit))
            workplace_dict[unit] = workplace_list
        return {
            'organization': organization,
            'unit_list': unit_list,
            'workplace_dict': workplace_dict,
            'vue2_cdn': VUE2_CDN,
            'vue3_cdn': VUE3_CDN,
            'env_stage': ENV_STAGE,
            'use_huey': USE_HUEY,
        }
    else:
        return {

        }
