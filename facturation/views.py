from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BonCommande, Facture, Proforma, DemandeAnalyse
from .serializers import BonCommandeSerializer, FactureSerializer, ProformaSerializer, DemandeAnalyseSerializer
from clients.permissions_catalog import user_has_permission

from io import BytesIO


def _draw_responsable_signature(canvas_obj, x, y, document):
    """Dessine le bloc signature + cachet du responsable labo sur un PDF
    (Devis/Bon de commande/Facture) si la validation a ete appliquee."""
    if not document.signature_responsable_appliquee or not document.valide_par_responsable:
        return

    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader

    profile = getattr(document.valide_par_responsable, "client_profile", None)
    if profile is None:
        return

    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#334155"))
    canvas_obj.drawString(x, y, "Le Responsable Laboratoire")

    image_y = y - 32
    if profile.cachet_image:
        try:
            canvas_obj.drawImage(
                ImageReader(profile.cachet_image), x, image_y,
                width=26 * mm, height=26 * mm, preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass
    if profile.signature_image:
        try:
            canvas_obj.drawImage(
                ImageReader(profile.signature_image), x + 28 * mm, image_y + 4 * mm,
                width=35 * mm, height=18 * mm, preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass

    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(colors.HexColor("#334155"))
    canvas_obj.drawString(x, image_y - 5 * mm, document.valide_par_responsable.get_full_name() or document.valide_par_responsable.username)
    canvas_obj.setFillColor(colors.black)


def _creer_demande_analyse_si_absente(facture):
    """Cree la DemandeAnalyse liee a une facture payee, si elle n'existe pas
    deja. Partage entre `FactureViewSet.valider_paiement` (paiement declare
    par le client puis valide en comptabilite) et `FactureViewSet.encaisser`
    (paiement encaisse directement au guichet) : dans les deux cas, c'est la
    confirmation du paiement qui declenche la reception des echantillons."""

    if facture.proforma is None or facture.proforma.demande_devis is None:
        return
    if DemandeAnalyse.objects.filter(facture=facture).exists():
        return
    # Meme suffixe numerique que la facture (elle-meme alignee sur la
    # proforma/demande de devis), pour garder un numero de dossier coherent
    # de bout en bout : DEV-00013 / PROF-00013 / FAC-00013 / DA-00013.
    da_numero = f"DA-{facture.numero.split('-')[-1]}"
    if DemandeAnalyse.objects.filter(numero=da_numero).exists():
        da_numero = f"DA-{DemandeAnalyse.objects.count() + 1:05d}"
    DemandeAnalyse.objects.create(
        numero=da_numero,
        client=facture.client,
        demande_devis=facture.proforma.demande_devis,
        proforma=facture.proforma,
        facture=facture,
        montant_ht=facture.montant_ht,
        montant_ttc=facture.montant_ttc,
        statut="EN_ATTENTE_ECHANTILLONS",
    )


def _generer_recu_caisse_pdf(facture, mode_paiement, reference, agent):
    """Genere un recu de paiement (PDF) pour un encaissement effectue au
    guichet : sert de justificatif auto-genere, sans que le client ou le
    caissier n'aient a fournir de photo/scan."""

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas

    buffer = BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    primary = colors.HexColor("#0B57A4")

    c.setFillColor(primary)
    c.rect(0, height - 40 * mm, width, 40 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(18 * mm, height - 20 * mm, "LANEMA")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 18 * mm, height - 18 * mm, "REÇU DE PAIEMENT")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 18 * mm, height - 26 * mm, f"N° RECU-{facture.numero}")
    c.drawRightString(width - 18 * mm, height - 32 * mm, f"Date: {timezone.now().date().strftime('%d/%m/%Y')}")

    y = height - 55 * mm
    c.setFillColor(colors.HexColor("#F3F6FB"))
    c.roundRect(18 * mm, y - 30 * mm, width - 36 * mm, 28 * mm, 6, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(22 * mm, y - 9 * mm, "Reçu de")
    c.setFont("Helvetica", 10)
    client_name = getattr(getattr(facture.client, "client_profile", None), "raison_sociale", "") or facture.client.email
    c.drawString(22 * mm, y - 15 * mm, client_name)
    c.drawString(22 * mm, y - 20 * mm, facture.client.email)
    c.drawString(22 * mm, y - 25 * mm, f"Pour règlement de la facture {facture.numero}")

    mode_label = dict(facture.MODE_PAIEMENT_CHOICES).get(mode_paiement, mode_paiement)
    ligne_y = y - 45 * mm
    c.setFont("Helvetica", 11)
    c.drawString(18 * mm, ligne_y, "Mode de paiement")
    c.drawRightString(width - 18 * mm, ligne_y, mode_label)
    if reference:
        ligne_y -= 8 * mm
        c.drawString(18 * mm, ligne_y, "Référence")
        c.drawRightString(width - 18 * mm, ligne_y, reference)

    ligne_y -= 14 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(18 * mm, ligne_y, "Montant encaissé")
    c.drawRightString(width - 18 * mm, ligne_y, f"{facture.montant_ttc} {facture.devise}")

    agent_profile = getattr(agent, "client_profile", None)
    agent_name = agent.get_full_name() or agent.username
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(18 * mm, 30 * mm, f"Encaissé par : {agent_name}")
    if agent_profile is not None and getattr(agent_profile, "cachet_image", None):
        try:
            from reportlab.lib.utils import ImageReader
            c.drawImage(
                ImageReader(agent_profile.cachet_image), width - 18 * mm - 26 * mm, 20 * mm,
                width=26 * mm, height=26 * mm, preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass

    c.setFillColor(colors.HexColor("#2D7EDB"))
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, 15 * mm, "Merci pour votre confiance !")
    c.setFillColor(colors.black)

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _draw_client_signature(canvas_obj, x, y, bon_commande):
    """Dessine la signature electronique (dessinee) du client sur le PDF du
    Bon de commande, si elle a ete apposee."""
    if not bon_commande.signature_client_image:
        return

    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader

    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#334155"))
    canvas_obj.drawString(x, y, "Signature du client")
    try:
        canvas_obj.drawImage(
            ImageReader(bon_commande.signature_client_image), x, y - 34 * mm,
            width=65 * mm, height=32 * mm, preserveAspectRatio=True, mask="auto",
        )
    except Exception:
        pass
    canvas_obj.setFillColor(colors.black)


class ProformaViewSet(viewsets.ModelViewSet):
    queryset = Proforma.objects.select_related("client").all()
    serializer_class = ProformaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="valider")
    def valider(self, request, pk=None):
        """Valider une proforma côté administration.

        Pour l'instant, on met simplement à jour le statut pour indiquer
        qu'elle est prête à être proposée au client.
        """

        proforma = self.get_object()
        # Passer la proforma au statut VALIDEE pour déclencher la phase de décision côté client.
        proforma.statut = "VALIDEE"
        proforma.save(update_fields=["statut"])

        serializer = self.get_serializer(proforma)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="valider_responsable")
    def valider_responsable(self, request, pk=None):
        """Apposer la signature + le cachet du responsable labo sur le devis.

        L'utilisateur courant doit avoir renseigné sa signature et son cachet
        dans son ClientProfile (roles ADMIN/GESTIONNAIRE).
        """

        proforma = self.get_object()
        user = request.user
        profile = getattr(user, "client_profile", None)

        if not user_has_permission(user, "facturation.valider_responsable"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        if not profile.signature_image or not profile.cachet_image:
            return Response(
                {"detail": "Veuillez d'abord enregistrer votre signature et votre cachet dans votre profil"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proforma.valide_par_responsable = user
        proforma.date_validation_responsable = timezone.now().date()
        proforma.signature_responsable_appliquee = True
        proforma.save(update_fields=[
            "valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee",
        ])

        serializer = self.get_serializer(proforma)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="telecharger_pdf")
    def telecharger_pdf(self, request, pk=None):
        """Retourner un PDF de proforma encodé en base64.

        Pour éviter certains blocages côté navigateur sur les réponses PDF
        directes, on renvoie ici un JSON avec le contenu encodé en base64.
        Le frontend reconstruit ensuite le fichier.
        """

        import base64

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle

        proforma = self.get_object()

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        primary = colors.HexColor("#0B57A4")

        # Header
        c.setFillColor(primary)
        c.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(18 * mm, height - 22 * mm, "LANEMA")
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(width - 18 * mm, height - 20 * mm, "DEVIS")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, height - 28 * mm, f"N° {proforma.numero}")
        c.drawRightString(
            width - 18 * mm,
            height - 34 * mm,
            f"Date: {proforma.date_emission.strftime('%d/%m/%Y') if proforma.date_emission else ''}",
        )

        # Client box
        y = height - 58 * mm
        c.setFillColor(colors.HexColor("#F3F6FB"))
        c.roundRect(18 * mm, y - 25 * mm, width - 36 * mm, 22 * mm, 6, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(22 * mm, y - 9 * mm, "Client")
        c.setFont("Helvetica", 10)
        client_name = getattr(getattr(proforma.client, "client_profile", None), "raison_sociale", "") or proforma.client.email
        c.drawString(22 * mm, y - 15 * mm, client_name)
        c.drawString(22 * mm, y - 20 * mm, proforma.client.email)

        # Table (simple, 1 ligne)
        data = [["Description", "Tarif", "Qté", "Montant"]]
        description = f"Prestations laboratoire - {proforma.demande_devis.numero if proforma.demande_devis else 'Demande'}"
        data.append([description, "-", "1", f"{proforma.montant_ttc} {proforma.devise}"])

        table = Table(data, colWidths=[90 * mm, 30 * mm, 20 * mm, 35 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D7EE")),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ]
            )
        )
        tw, th = table.wrapOn(c, width - 36 * mm, 100 * mm)
        table.drawOn(c, 18 * mm, y - 60 * mm)

        # Totals
        total_y = y - 110 * mm
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, total_y, f"Sous total: {proforma.montant_ht} {proforma.devise}")
        tva = (float(proforma.montant_ttc) - float(proforma.montant_ht)) if proforma.montant_ttc is not None and proforma.montant_ht is not None else 0
        c.drawRightString(width - 18 * mm, total_y - 6 * mm, f"TVA: {tva:.2f} {proforma.devise}")
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(width - 18 * mm, total_y - 13 * mm, f"Total: {proforma.montant_ttc} {proforma.devise}")

        # Signature responsable labo
        _draw_responsable_signature(c, 18 * mm, total_y - 30 * mm, proforma)

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.HexColor("#2D7EDB"))
        c.drawCentredString(width / 2, 20 * mm, "Merci pour votre confiance !")
        c.setFillColor(colors.black)

        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        content_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        filename = f"Devis_{proforma.numero}.pdf"

        return Response({"filename": filename, "content": content_b64})

    @action(detail=True, methods=["post"], url_path="ajuster_montants")
    def ajuster_montants(self, request, pk=None):
        """Ajuster les montants d'une proforma côté administration.

        Le frontend envoie un JSON pouvant contenir :
        - montant_ht
        - montant_ttc
        - montant_tva (ignoré pour l'instant, non stocké directement)
        - notes_revision (ignoré pour l'instant ou loggué plus tard)
        """

        proforma = self.get_object()
        data = request.data or {}

        fields_to_update: list[str] = []

        montant_ht = data.get("montant_ht")
        if montant_ht is not None:
            try:
                proforma.montant_ht = montant_ht
                fields_to_update.append("montant_ht")
            except Exception:
                pass

        montant_ttc = data.get("montant_ttc")
        if montant_ttc is not None:
            try:
                proforma.montant_ttc = montant_ttc
                fields_to_update.append("montant_ttc")
            except Exception:
                pass

        if fields_to_update:
            proforma.save(update_fields=fields_to_update)

        serializer = self.get_serializer(proforma)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="accepter")
    def accepter(self, request, pk=None):
        """Accepter une proforma côté client.

        Met le statut à ACCEPTEE. La création de la Demande d'Analyse
        associée pourra être gérée ici ou dans un autre module.
        """

        proforma = self.get_object()
        proforma.statut = "ACCEPTEE"
        proforma.save(update_fields=["statut"])

        # Synchroniser le statut du devis associé (utilisé par les stats dashboard)
        if proforma.demande_devis is not None:
            try:
                proforma.demande_devis.statut = "ACCEPTEE"
                proforma.demande_devis.save(update_fields=["statut"])
            except Exception:
                pass

        # Emettre simultanement le Bon de Commande et la Facture : le client doit
        # signer le premier et payer la seconde AVANT que la demande d'analyse
        # ne soit creee (la reception des echantillons n'intervient qu'apres
        # validation du paiement, cf. FactureViewSet.valider_paiement).
        #
        # Les deux documents reprennent le meme suffixe numerique que la
        # proforma (elle-meme alignee sur la demande de devis, cf.
        # DemandeDevisViewSet.perform_create) : DEV-00013 -> PROF-00013 ->
        # BC-00013 / FAC-00013 -> DA-00013, pour qu'un dossier reste
        # identifiable par un seul numero a travers tout le circuit.
        suffixe = proforma.numero.split("-")[-1]

        bon_commande = BonCommande.objects.filter(proforma=proforma).first()
        if bon_commande is None:
            bc_numero = f"BC-{suffixe}"
            if BonCommande.objects.filter(numero=bc_numero).exists():
                bc_numero = f"BC-{BonCommande.objects.count() + 1:05d}"
            bon_commande = BonCommande.objects.create(
                numero=bc_numero,
                client=proforma.client,
                proforma=proforma,
                montant_ht=proforma.montant_ht,
                montant_ttc=proforma.montant_ttc,
                devise=proforma.devise,
                statut="EMIS",
            )

        existing_facture = Facture.objects.filter(proforma=proforma).first()
        if existing_facture is None:
            fac_numero = f"FAC-{suffixe}"
            if Facture.objects.filter(numero=fac_numero).exists():
                fac_numero = f"FAC-{Facture.objects.count() + 1:05d}"
            date_emission = timezone.now().date()
            Facture.objects.create(
                numero=fac_numero,
                client=proforma.client,
                proforma=proforma,
                bon_commande=bon_commande,
                montant_ht=proforma.montant_ht,
                montant_ttc=proforma.montant_ttc,
                devise=proforma.devise,
                statut="EN_ATTENTE",
                date_emission=date_emission,
                date_echeance=date_emission + timedelta(days=30),
                visible_client=True,
            )

        serializer = self.get_serializer(proforma)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="refuser")
    def refuser(self, request, pk=None):
        """Refuser une proforma côté client.

        Met le statut à REFUSEE.
        """

        proforma = self.get_object()
        proforma.statut = "REFUSEE"
        proforma.save(update_fields=["statut"])

        # Synchroniser le statut du devis associé
        if proforma.demande_devis is not None:
            try:
                proforma.demande_devis.statut = "REFUSEE"
                proforma.demande_devis.save(update_fields=["statut"])
            except Exception:
                pass

        serializer = self.get_serializer(proforma)
        return Response(serializer.data)


class BonCommandeViewSet(viewsets.ModelViewSet):
    queryset = BonCommande.objects.select_related("client", "proforma").all()
    serializer_class = BonCommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(getattr(user, "client_profile", None), "role", None)
        if role == "CLIENT":
            return qs.filter(client=user)
        return qs

    @action(detail=True, methods=["post"], url_path="signer_client")
    def signer_client(self, request, pk=None):
        """Signature electronique (dessinee) du client sur le bon de commande.

        Le frontend envoie l'image de la signature (pad tactile) dans le
        champ ``signature_client_image`` en multipart/form-data.
        """

        bon_commande = self.get_object()

        signature = request.FILES.get("signature_client_image")
        if signature is None:
            return Response(
                {"detail": "La signature du client est requise"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bon_commande.signature_client_image = signature
        bon_commande.date_signature_client = timezone.now().date()
        bon_commande.statut = "SIGNE_CLIENT"
        bon_commande.save(update_fields=[
            "signature_client_image", "date_signature_client", "statut",
        ])

        serializer = self.get_serializer(bon_commande, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="valider_responsable")
    def valider_responsable(self, request, pk=None):
        """Apposer la signature + le cachet du responsable labo sur le bon
        de commande (memes conditions que ProformaViewSet.valider_responsable)."""

        bon_commande = self.get_object()
        user = request.user
        profile = getattr(user, "client_profile", None)

        if not user_has_permission(user, "facturation.valider_responsable"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        if not profile.signature_image or not profile.cachet_image:
            return Response(
                {"detail": "Veuillez d'abord enregistrer votre signature et votre cachet dans votre profil"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bon_commande.valide_par_responsable = user
        bon_commande.date_validation_responsable = timezone.now().date()
        bon_commande.signature_responsable_appliquee = True
        bon_commande.save(update_fields=[
            "valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee",
        ])

        serializer = self.get_serializer(bon_commande)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="telecharger_pdf")
    def telecharger_pdf(self, request, pk=None):
        """Retourner le PDF du bon de commande encode en base64 (meme
        mecanisme que Proforma/Facture)."""

        import base64

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle

        bon_commande = self.get_object()

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        primary = colors.HexColor("#0B57A4")

        # Header
        c.setFillColor(primary)
        c.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(18 * mm, height - 22 * mm, "LANEMA")
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(width - 18 * mm, height - 20 * mm, "BON DE COMMANDE")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, height - 28 * mm, f"N° {bon_commande.numero}")
        c.drawRightString(
            width - 18 * mm,
            height - 34 * mm,
            f"Date: {bon_commande.date_emission.strftime('%d/%m/%Y') if bon_commande.date_emission else ''}",
        )

        # Client box
        y = height - 58 * mm
        c.setFillColor(colors.HexColor("#F3F6FB"))
        c.roundRect(18 * mm, y - 25 * mm, width - 36 * mm, 22 * mm, 6, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(22 * mm, y - 9 * mm, "Client")
        c.setFont("Helvetica", 10)
        client_name = getattr(getattr(bon_commande.client, "client_profile", None), "raison_sociale", "") or bon_commande.client.email
        c.drawString(22 * mm, y - 15 * mm, client_name)
        c.drawString(22 * mm, y - 20 * mm, bon_commande.client.email)

        # Table (simple, 1 ligne)
        data = [["Description", "Tarif", "Qté", "Montant"]]
        description = f"Prestations laboratoire - Devis {bon_commande.proforma.numero if bon_commande.proforma else ''}"
        data.append([description, "-", "1", f"{bon_commande.montant_ttc} {bon_commande.devise}"])

        table = Table(data, colWidths=[90 * mm, 30 * mm, 20 * mm, 35 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D7EE")),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ]
            )
        )
        table.wrapOn(c, width - 36 * mm, 100 * mm)
        table.drawOn(c, 18 * mm, y - 60 * mm)

        # Totals
        total_y = y - 110 * mm
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, total_y, f"Sous total: {bon_commande.montant_ht} {bon_commande.devise}")
        tva = (float(bon_commande.montant_ttc) - float(bon_commande.montant_ht)) if bon_commande.montant_ttc is not None and bon_commande.montant_ht is not None else 0
        c.drawRightString(width - 18 * mm, total_y - 6 * mm, f"TVA: {tva:.2f} {bon_commande.devise}")
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(width - 18 * mm, total_y - 13 * mm, f"Total: {bon_commande.montant_ttc} {bon_commande.devise}")

        # Signatures : responsable labo (gauche) + client (droite)
        _draw_responsable_signature(c, 18 * mm, total_y - 30 * mm, bon_commande)
        _draw_client_signature(c, width / 2 + 10 * mm, total_y - 30 * mm, bon_commande)

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.HexColor("#2D7EDB"))
        c.drawCentredString(width / 2, 18 * mm, "Merci pour votre confiance !")
        c.setFillColor(colors.black)

        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        content_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        filename = f"BonCommande_{bon_commande.numero}.pdf"

        return Response({"filename": filename, "content": content_b64})


class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.select_related("client").all()
    serializer_class = FactureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Les clients ne voient que leurs propres factures
        try:
            role = getattr(getattr(user, "client_profile", None), "role", None)
        except Exception:  # pragma: no cover - simple safeguard
            role = None

        if role == "CLIENT":
            return qs.filter(client=user)
        return qs

    def perform_create(self, serializer):
        client = serializer.validated_data.get("client") or self.request.user
        if not serializer.validated_data.get("numero"):
            last_id = Facture.objects.count() + 1
            numero = f"FAC-{last_id:05d}"
        else:
            numero = serializer.validated_data["numero"]
        # Les factures sont automatiquement visibles aux clients
        serializer.save(client=client, numero=numero, visible_client=True)

    @action(detail=True, methods=["post"], url_path="payer")
    def payer(self, request, pk=None):
        """Enregistrer un paiement (client).

        - mode_paiement: "CHEQUE" ou "COMPTANT" (obligatoire)
        - justificatif_paiement: fichier uploadé (photo du chèque, reçu...)

        La facture passe en statut EN_ATTENTE_VALIDATION et sera ensuite
        validée côté comptabilité via l'action ``valider_paiement``.
        """

        facture = self.get_object()

        # Le client doit d'abord signer son bon de commande, ET le responsable
        # labo doit l'avoir validé (signature + cachet), avant de pouvoir payer
        # la facture correspondante.
        if facture.bon_commande is None or facture.bon_commande.statut != "SIGNE_CLIENT":
            return Response(
                {"detail": "Vous devez d'abord signer votre bon de commande avant de procéder au paiement."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not facture.bon_commande.signature_responsable_appliquee:
            return Response(
                {"detail": "Le bon de commande doit d'abord être validé par le responsable du laboratoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mode_paiement = request.data.get("mode_paiement")
        if mode_paiement not in dict(Facture.MODE_PAIEMENT_CHOICES):
            return Response(
                {"detail": "mode_paiement invalide"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        justificatif = request.FILES.get("justificatif_paiement")
        if justificatif is None:
            return Response(
                {"detail": "Un justificatif de paiement est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reference = request.data.get("reference_paiement", "").strip()

        facture.mode_paiement = mode_paiement
        facture.justificatif_paiement = justificatif
        facture.statut = "EN_ATTENTE_VALIDATION"
        if reference:
            facture.reference_paiement = reference
        facture.save(
            update_fields=[
                "mode_paiement",
                "justificatif_paiement",
                "statut",
                "reference_paiement",
            ]
        )

        serializer = self.get_serializer(facture, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="valider_responsable")
    def valider_responsable(self, request, pk=None):
        """Apposer la signature + le cachet du responsable labo sur la
        facture (memes conditions que ProformaViewSet.valider_responsable)."""

        facture = self.get_object()
        user = request.user
        profile = getattr(user, "client_profile", None)

        if not user_has_permission(user, "facturation.valider_responsable"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        if not profile.signature_image or not profile.cachet_image:
            return Response(
                {"detail": "Veuillez d'abord enregistrer votre signature et votre cachet dans votre profil"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        facture.valide_par_responsable = user
        facture.date_validation_responsable = timezone.now().date()
        facture.signature_responsable_appliquee = True
        facture.save(update_fields=[
            "valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee",
        ])

        serializer = self.get_serializer(facture)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="telecharger_pdf")
    def telecharger_pdf(self, request, pk=None):  # pragma: no cover - simple file response
        """Téléchargement basique du PDF de facture.

        Retourne un JSON avec le PDF encodé en base64 pour éviter les
        problèmes CORS et les interceptions par les gestionnaires de téléchargement.
        """
        import base64

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle

        facture = self.get_object()

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        primary = colors.HexColor("#0B57A4")

        # Header
        c.setFillColor(primary)
        c.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(18 * mm, height - 22 * mm, "LANEMA")
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(width - 18 * mm, height - 20 * mm, "FACTURE")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, height - 28 * mm, f"N° {facture.numero}")
        c.drawRightString(
            width - 18 * mm,
            height - 34 * mm,
            f"Date: {facture.date_emission.strftime('%d/%m/%Y') if facture.date_emission else ''}",
        )

        # Client box
        y = height - 58 * mm
        c.setFillColor(colors.HexColor("#F3F6FB"))
        c.roundRect(18 * mm, y - 25 * mm, width - 36 * mm, 22 * mm, 6, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(22 * mm, y - 9 * mm, "Client")
        c.setFont("Helvetica", 10)
        client_name = getattr(getattr(facture.client, "client_profile", None), "raison_sociale", "") or facture.client.email
        c.drawString(22 * mm, y - 15 * mm, client_name)
        c.drawString(22 * mm, y - 20 * mm, facture.client.email)

        # Table (simple, 1 ligne)
        data = [["Description", "Tarif", "Qté", "Montant"]]
        data.append([
            f"Analyses laboratoire - {facture.numero}",
            "-",
            "1",
            f"{facture.montant_ttc} {facture.devise}",
        ])

        table = Table(data, colWidths=[90 * mm, 30 * mm, 20 * mm, 35 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D7EE")),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ]
            )
        )
        table.wrapOn(c, width - 36 * mm, 100 * mm)
        table.drawOn(c, 18 * mm, y - 60 * mm)

        # Totals
        total_y = y - 110 * mm
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, total_y, f"Sous total: {facture.montant_ht} {facture.devise}")
        tva = (float(facture.montant_ttc) - float(facture.montant_ht)) if facture.montant_ttc is not None and facture.montant_ht is not None else 0
        c.drawRightString(width - 18 * mm, total_y - 6 * mm, f"TVA: {tva:.2f} {facture.devise}")
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(width - 18 * mm, total_y - 13 * mm, f"Total: {facture.montant_ttc} {facture.devise}")

        # Signature responsable labo
        _draw_responsable_signature(c, 18 * mm, total_y - 30 * mm, facture)

        # Footer / paiement
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(18 * mm, 32 * mm, f"Mode de paiement : {facture.mode_paiement or '-'}")
        if facture.date_echeance:
            c.drawString(18 * mm, 26 * mm, f"Date d'échéance : {facture.date_echeance.strftime('%d/%m/%Y')}")
        c.setFillColor(colors.HexColor("#2D7EDB"))
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width / 2, 18 * mm, "Merci pour votre confiance !")
        c.setFillColor(colors.black)

        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        content_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        filename = f"Facture_{facture.numero}.pdf"

        return Response({"filename": filename, "pdf_base64": content_b64})

    @action(detail=True, methods=["post"], url_path="valider_paiement")
    def valider_paiement(self, request, pk=None):
        """Validation comptable du paiement.

        Accessible aux utilisateurs ayant un rôle de gestion interne
        (ADMIN, GESTIONNAIRE, COMPTABLE le cas échéant).
        """

        facture = self.get_object()
        user = request.user

        if not user_has_permission(user, "facturation.valider_paiement"):
            return Response(
                {"detail": "Non autorisé"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if facture.statut != "EN_ATTENTE_VALIDATION":
            return Response(
                {"detail": "Cette facture n'est pas en attente de validation de paiement."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        facture.paiement_valide = True
        facture.visible_client = True
        facture.statut = "PAYEE"
        facture.date_paiement = facture.date_paiement or timezone.now().date()
        facture.save(
            update_fields=[
                "paiement_valide",
                "visible_client",
                "statut",
                "date_paiement",
            ]
        )

        # Le paiement etant valide, la demande d'analyse peut demarrer : le
        # labo va pouvoir receptionner les echantillons. Cree ici plutot qu'a
        # l'acceptation du devis, puisque le client doit desormais payer AVANT
        # que l'analyse ne soit engagee.
        _creer_demande_analyse_si_absente(facture)

        serializer = self.get_serializer(facture, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="encaisser")
    def encaisser(self, request, pk=None):
        """Encaissement direct au guichet (module caisse) : le comptable ou
        le responsable confirme avoir recu le paiement en main propre.

        Contrairement a `payer` (declaration client, a valider ensuite) et
        `valider_paiement` (validation d'une preuve deja deposee), cette
        action finalise le paiement en une seule etape : aucun justificatif
        a televerser, un recu PDF est genere automatiquement et sert de
        preuve de paiement (visible cote client comme les autres justificatifs).
        """

        facture = self.get_object()
        user = request.user

        if not user_has_permission(user, "facturation.encaisser"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        if facture.statut not in ("EN_ATTENTE", "RETARD", "EN_ATTENTE_VALIDATION"):
            return Response(
                {"detail": "Cette facture ne peut pas être encaissée dans son état actuel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Meme regle metier que pour un paiement en ligne : le bon de
        # commande doit avoir ete signe par le client et valide par le
        # responsable avant tout encaissement, quel que soit le canal.
        if facture.bon_commande is None or facture.bon_commande.statut != "SIGNE_CLIENT":
            return Response(
                {"detail": "Le client doit d'abord signer son bon de commande avant tout encaissement."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not facture.bon_commande.signature_responsable_appliquee:
            return Response(
                {"detail": "Le bon de commande doit d'abord être validé par le responsable du laboratoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mode_paiement = request.data.get("mode_paiement")
        if mode_paiement not in dict(Facture.MODE_PAIEMENT_CHOICES):
            return Response({"detail": "mode_paiement invalide"}, status=status.HTTP_400_BAD_REQUEST)

        reference = (request.data.get("reference_paiement") or "").strip()

        from django.core.files.base import ContentFile

        recu_pdf = _generer_recu_caisse_pdf(facture, mode_paiement, reference, user)

        facture.mode_paiement = mode_paiement
        if reference:
            facture.reference_paiement = reference
        facture.justificatif_paiement.save(
            f"recu_{facture.numero}.pdf", ContentFile(recu_pdf), save=False
        )
        facture.paiement_valide = True
        facture.visible_client = True
        facture.statut = "PAYEE"
        facture.date_paiement = timezone.now().date()
        facture.save(
            update_fields=[
                "mode_paiement",
                "reference_paiement",
                "justificatif_paiement",
                "paiement_valide",
                "visible_client",
                "statut",
                "date_paiement",
            ]
        )

        _creer_demande_analyse_si_absente(facture)

        serializer = self.get_serializer(facture, context={"request": request})
        return Response(serializer.data)


class FacturationStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Facture.objects.all()
        total = qs.aggregate(total=Sum("montant_ttc")) if qs.exists() else {"total": 0}
        data = {
            "total_factures": qs.count(),
            "payees": qs.filter(statut="PAYEE").count(),
            "en_attente": qs.filter(statut="EN_ATTENTE").count(),
            "montant_total_ttc": float(total.get("total") or 0),
        }
        return Response(data)



class DemandeAnalyseViewSet(viewsets.ModelViewSet):
    queryset = DemandeAnalyse.objects.select_related("client", "demande_devis", "proforma", "facture").all()
    serializer_class = DemandeAnalyseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(getattr(user, "client_profile", None), "role", None)
        if role == "CLIENT":
            return qs.filter(client=user)
        return qs

    def perform_create(self, serializer):
        # Génération simple d'un numéro DA-00001
        if not serializer.validated_data.get("numero"):
            last_id = DemandeAnalyse.objects.count() + 1
            numero = f"DA-{last_id:05d}"
        else:
            numero = serializer.validated_data["numero"]
        serializer.save(numero=numero)

    @action(detail=True, methods=["post"], url_path="confirmer_depot_echantillons")
    def confirmer_depot_echantillons(self, request, pk=None):
        analyse = self.get_object()

        if not user_has_permission(request.user, "echantillons.manage"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        if analyse.facture is None or analyse.facture.statut != "PAYEE":
            return Response(
                {"detail": "Le paiement doit être validé avant la réception des échantillons."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if analyse.statut != "EN_ATTENTE_ECHANTILLONS":
            return Response(
                {"detail": "Cette demande n'est pas en attente de dépôt d'échantillons."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        analyse.statut = "ECHANTILLONS_RECUS"
        analyse.date_depot_echantillons = timezone.now().date()
        analyse.save(update_fields=["statut", "date_depot_echantillons"])
        serializer = self.get_serializer(analyse)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="telecharger_rapport")
    def telecharger_rapport(self, request, pk=None):
        """Retourner un rapport de résultats encodé en base64.

        Pour éviter certains blocages côté navigateur sur les réponses PDF
        directes, on renvoie ici un JSON contenant le contenu du rapport
        encodé en base64. Le frontend se charge de reconstruire le fichier.
        """

        import base64

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.utils import simpleSplit

        analyse = self.get_object()
        demande = analyse.demande_devis

        # Les echantillons sont desormais lies a la DemandeAnalyse (reception
        # apres paiement), et non plus a la DemandeDevis.
        echantillon = analyse.echantillons.order_by("-created_at").first()

        def normalize_value(v):
            s = str(v or "").strip()
            return s if s else "-"

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        primary = colors.HexColor("#0B57A4")

        def draw_wrapped_text(x: float, y: float, text: str, max_width: float, font_name: str = "Helvetica", font_size: int = 10, leading: float = 12):
            c.setFont(font_name, font_size)
            lines = simpleSplit(text or "", font_name, font_size, max_width)
            current_y = y
            for line in lines:
                c.drawString(x, current_y, line)
                current_y -= leading
            return current_y

        # Header
        c.setFillColor(primary)
        c.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(18 * mm, height - 22 * mm, "LAB MANAGER")
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(width - 18 * mm, height - 20 * mm, "RAPPORT")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 18 * mm, height - 28 * mm, f"N° {analyse.numero}")
        date_doc = analyse.date_fin_analyse or analyse.date_debut_analyse or (analyse.date_creation.date() if analyse.date_creation else None)
        c.drawRightString(
            width - 18 * mm,
            height - 34 * mm,
            f"Date: {date_doc.strftime('%d/%m/%Y') if date_doc else ''}",
        )

        # Client box
        y = height - 58 * mm
        c.setFillColor(colors.HexColor("#F3F6FB"))
        c.roundRect(18 * mm, y - 25 * mm, width - 36 * mm, 22 * mm, 6, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(22 * mm, y - 9 * mm, "Client")
        c.setFont("Helvetica", 10)
        client_name = getattr(getattr(analyse.client, "client_profile", None), "raison_sociale", "") or analyse.client.email
        c.drawString(22 * mm, y - 15 * mm, client_name)
        c.drawString(22 * mm, y - 20 * mm, analyse.client.email)

        # Bloc demande (infos saisies par le client)
        block_y = y - 35 * mm
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(18 * mm, block_y, "Détails de la demande")

        meta_rows = []
        meta_rows.append(["Demande de devis", demande.numero if demande else "-"])
        meta_rows.append(["Type d'analyse", getattr(demande, "type_analyse", "-") or "-"])
        meta_rows.append(["Catégorie", getattr(demande, "categorie", "-") or "-"])
        meta_rows.append([
            "Désignation",
            normalize_value(getattr(echantillon, "designation", "")) if echantillon else "-",
        ])
        meta_rows.append([
            "Type d'échantillon",
            normalize_value(getattr(echantillon, "type_echantillon", "")) if echantillon else "-",
        ])
        meta_rows.append([
            "Quantité",
            normalize_value(getattr(echantillon, "quantite", "")) if echantillon else "-",
        ])
        meta_rows.append(["Statut analyse", analyse.statut])
        meta_rows.append(["Début analyse", analyse.date_debut_analyse.strftime('%d/%m/%Y') if analyse.date_debut_analyse else "-"])
        meta_rows.append(["Fin analyse", analyse.date_fin_analyse.strftime('%d/%m/%Y') if analyse.date_fin_analyse else "-"])

        meta_table = Table(meta_rows, colWidths=[45 * mm, width - 36 * mm - 45 * mm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D7EE")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        _, meta_h = meta_table.wrap(width - 36 * mm, 200 * mm)
        meta_table.drawOn(c, 18 * mm, block_y - 6 * mm - meta_h)

        # Description
        desc_title_y = block_y - 8 * mm - meta_h - 10 * mm
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(18 * mm, desc_title_y, "Description")
        c.setFillColor(colors.HexColor("#334155"))
        desc_text = getattr(demande, "description", "") if demande else ""
        next_y = draw_wrapped_text(
            18 * mm,
            desc_title_y - 8 * mm,
            desc_text or "-",
            width - 36 * mm,
            font_name="Helvetica",
            font_size=10,
            leading=12,
        )

        # Résultats / observations
        results_title_y = next_y - 6 * mm
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(18 * mm, results_title_y, "Résultats / Observations")
        c.setFillColor(colors.HexColor("#334155"))
        obs = analyse.observations or "-"
        next_y2 = draw_wrapped_text(
            18 * mm,
            results_title_y - 8 * mm,
            obs,
            width - 36 * mm,
            font_name="Helvetica",
            font_size=10,
            leading=12,
        )

        # Montants (pour cohérence avec devis/facture)
        total_y = max(30 * mm, next_y2 - 10 * mm)
        c.setFont("Helvetica", 10)
        devise = getattr(analyse.proforma, "devise", "XAF") if getattr(analyse, "proforma", None) else "XAF"
        c.drawRightString(width - 18 * mm, total_y, f"Sous total: {analyse.montant_ht} {devise}")
        tva = (float(analyse.montant_ttc) - float(analyse.montant_ht)) if analyse.montant_ttc is not None and analyse.montant_ht is not None else 0
        c.drawRightString(width - 18 * mm, total_y - 6 * mm, f"TVA: {tva:.2f} {devise}")
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(width - 18 * mm, total_y - 13 * mm, f"Total: {analyse.montant_ttc} {devise}")

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.HexColor("#2D7EDB"))
        c.drawCentredString(width / 2, 18 * mm, "Merci pour votre confiance !")
        c.setFillColor(colors.black)

        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        content_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        filename = f"Rapport_{analyse.numero}.pdf"

        return Response({"filename": filename, "content": content_b64})

    @action(detail=True, methods=["post"], url_path="demarrer_analyse")
    def demarrer_analyse(self, request, pk=None):
        analyse = self.get_object()

        if not user_has_permission(request.user, "essais.manage"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        if analyse.statut != "ECHANTILLONS_RECUS":
            return Response(
                {"detail": "Les échantillons doivent être réceptionnés avant de démarrer l'analyse."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        analyse.statut = "EN_COURS"
        analyse.date_debut_analyse = timezone.now().date()
        analyse.save(update_fields=["statut", "date_debut_analyse"])

        # Synchroniser le statut du devis associé
        if getattr(analyse, "demande_devis", None) is not None:
            try:
                analyse.demande_devis.statut = "EN_COURS"
                analyse.demande_devis.save(update_fields=["statut"])
            except Exception:
                pass

        serializer = self.get_serializer(analyse)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="terminer_analyse")
    def terminer_analyse(self, request, pk=None):
        analyse = self.get_object()

        if not user_has_permission(request.user, "essais.manage"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        if analyse.statut != "EN_COURS":
            return Response(
                {"detail": "L'analyse doit être en cours avant de pouvoir être clôturée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        observations = request.data.get("observations", "")
        analyse.statut = "TERMINEE"
        analyse.date_fin_analyse = timezone.now().date()
        if observations:
            analyse.observations = observations
        analyse.save(update_fields=["statut", "date_fin_analyse", "observations"])

        # La facture est desormais emise et payee AVANT le demarrage de
        # l'analyse (cf. ProformaViewSet.accepter / FactureViewSet.valider_paiement) :
        # aucune creation de facture n'a plus lieu ici.

        serializer = self.get_serializer(analyse)
        return Response(serializer.data)


def compute_financiers_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI financiers du laboratoire."""
    from qualite.models import Essai

    factures = Facture.objects.all()
    demandes_analyses = DemandeAnalyse.objects.all()
    if date_debut and date_fin:
        factures = factures.filter(date_emission__range=(date_debut, date_fin))
        demandes_analyses = demandes_analyses.filter(date_creation__date__range=(date_debut, date_fin))

    ca_analyses = factures.filter(statut="PAYEE").aggregate(t=Sum("montant_ttc"))["t"] or 0

    recettes_par_labo = list(
        demandes_analyses.exclude(laboratoire__isnull=True)
        .values("laboratoire__nom")
        .annotate(total=Sum("montant_ttc"))
        .order_by("-total")
    )

    essais_avec_cout = Essai.objects.filter(cout_revient__isnull=False)
    cout_moyen_analyse = essais_avec_cout.aggregate(m=Sum("cout_revient"))["m"]
    nb_essais_couts = essais_avec_cout.count()
    cout_moyen_analyse = round(float(cout_moyen_analyse) / nb_essais_couts, 2) if nb_essais_couts else None

    cout_consommables = 0
    try:
        from stock.models import MouvementStock

        sorties_analyse = MouvementStock.objects.filter(type_mouvement="SORTIE").select_related("article")
        if date_debut and date_fin:
            sorties_analyse = sorties_analyse.filter(date_mouvement__date__range=(date_debut, date_fin))
        cout_consommables = sum(
            float(m.quantite) * float(m.article.prix_unitaire) for m in sorties_analyse if m.article
        )
    except Exception:
        cout_consommables = None

    marge_par_type = []
    for type_essai in Essai.objects.exclude(type_essai="").values_list("type_essai", flat=True).distinct():
        essais_type = Essai.objects.filter(type_essai=type_essai)
        cout_total = sum(float(e.cout_revient) for e in essais_type if e.cout_revient is not None)
        # Echantillon.demande pointe desormais vers DemandeAnalyse (et non plus
        # DemandeDevis) : on somme directement les montants de ces demandes.
        demandes_analyse_ids = essais_type.exclude(echantillon__demande__isnull=True).values_list(
            "echantillon__demande_id", flat=True
        ).distinct()
        revenu_total = DemandeAnalyse.objects.filter(id__in=demandes_analyse_ids).aggregate(
            t=Sum("montant_ttc")
        )["t"] or 0
        marge_par_type.append({
            "type_essai": type_essai,
            "revenu": float(revenu_total),
            "cout": cout_total,
            "marge": float(revenu_total) - cout_total,
        })

    nb_factures = factures.count()
    nb_payees = factures.filter(statut="PAYEE").count()
    taux_recouvrement = round(nb_payees / nb_factures * 100, 1) if nb_factures else None

    montant_en_attente = factures.filter(
        statut__in=["EN_ATTENTE", "EN_ATTENTE_VALIDATION"]
    ).aggregate(t=Sum("montant_ttc"))["t"] or 0

    return {
        "chiffre_affaires_analyses": float(ca_analyses),
        "recettes_par_laboratoire": recettes_par_labo,
        "cout_moyen_analyse": cout_moyen_analyse,
        "cout_consommables": cout_consommables,
        "marge_par_type_essai": marge_par_type,
        "nombre_factures_emises": nb_factures,
        "taux_recouvrement": taux_recouvrement,
        "montant_prestations_en_attente_paiement": float(montant_en_attente),
    }


class FinanciersKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_financiers_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
