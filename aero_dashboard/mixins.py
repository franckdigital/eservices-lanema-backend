"""Traçabilité DAE reutilisable — cf. Phase 3 du plan (HistoriqueActionDAE).

log_historique_dae() est la primitive de base, appelable directement depuis
n'importe quelle vue/action custom (ex: DemandeDAEViewSet.accepter, qui ne
passe pas par perform_update). HistoriqueMixin cable perform_create/
perform_update automatiquement pour les ViewSets DRF standards qui n'ont pas
deja leurs propres surcharges (NonConformiteDAEViewSet, ActionCorrectiveDAEViewSet,
FactureDAEViewSet) — pour OrdreTravailViewSet et DemandeDAEViewSet, qui
personnalisent deja perform_create, l'appel a log_historique_dae() est fait
manuellement a l'endroit concerne plutot que via ce mixin, pour eviter toute
ambiguite d'ordre de resolution (MRO)."""
from django.contrib.contenttypes.models import ContentType

from .models import HistoriqueActionDAE


def log_historique_dae(instance, user, action, ancienne_valeur='', nouvelle_valeur=''):
    HistoriqueActionDAE.objects.create(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        utilisateur=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        ancienne_valeur=str(ancienne_valeur) if ancienne_valeur else '',
        nouvelle_valeur=str(nouvelle_valeur) if nouvelle_valeur else '',
    )


class HistoriqueMixin:
    def perform_create(self, serializer):
        instance = serializer.save()
        log_historique_dae(instance, self.request.user, "Créé")

    def perform_update(self, serializer):
        instance = self.get_object()
        ancien_statut = getattr(instance, "statut", None)
        updated = serializer.save()
        nouveau_statut = getattr(updated, "statut", None)
        if ancien_statut is not None and ancien_statut != nouveau_statut:
            log_historique_dae(
                updated, self.request.user, "Statut modifié",
                ancienne_valeur=ancien_statut, nouvelle_valeur=nouveau_statut,
            )
