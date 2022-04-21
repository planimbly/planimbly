from apps.organizations.models import Organization, Unit, Workplace


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
            'workplace_dict': workplace_dict
        }
    else:
        return {

        }
