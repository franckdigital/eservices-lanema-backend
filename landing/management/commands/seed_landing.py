import os

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from landing.models import NewsArticle, FAQ, AIKeywordResponse

SEED_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "seed_assets")


class Command(BaseCommand):
    help = "Peuple la vitrine LANEMA avec des actualités, une FAQ et les réponses de l'assistant IA."

    def handle(self, *args, **options):
        self.seed_news()
        self.seed_faq()
        self.seed_ai_responses()
        self.stdout.write(self.style.SUCCESS("Vitrine LANEMA peuplée avec succès."))

    def seed_news(self):
        articles = [
            dict(
                title="Le LANEMA renforce son dispositif de sécurité sanitaire des aliments",
                excerpt="La Direction Générale du LANEMA annonce de nouveaux investissements dans les laboratoires d'analyses microbiologiques et chimiques dédiés aux produits alimentaires.",
                content=(
                    "Dans le cadre de sa mission de protection des consommateurs, le LANEMA poursuit la modernisation "
                    "de ses équipements d'analyse microbiologique et chimique des denrées alimentaires. Cette démarche "
                    "s'inscrit dans la stratégie portée par la Direction Générale visant à renforcer la sécurité "
                    "sanitaire des aliments consommés en Côte d'Ivoire, qu'ils soient produits localement ou importés.\n\n"
                    "Les nouveaux équipements permettront de réduire les délais d'analyse tout en élargissant le "
                    "spectre des contaminants recherchés : résidus de pesticides, métaux lourds, mycotoxines et "
                    "agents pathogènes. Les laboratoires concernés bénéficient d'un programme de mise à niveau "
                    "conforme aux exigences de l'accréditation ISO/IEC 17025.\n\n"
                    "Cette initiative s'inscrit également dans une logique de coopération avec les autres "
                    "administrations en charge du contrôle qualité, afin de renforcer la chaîne de confiance entre "
                    "producteurs, importateurs et consommateurs ivoiriens."
                ),
                category="COMMUNIQUE",
                is_featured=True,
                days_ago=3,
                image_file="securite-alimentaire.png",
            ),
            dict(
                title="Métrologie légale : campagne de vérification des pompes à carburant",
                excerpt="Le LANEMA organise une nouvelle campagne de vérification des pompes à carburant sur l'ensemble du territoire national.",
                content=(
                    "Les équipes de métrologie du LANEMA sillonnent les stations-service du pays pour vérifier la "
                    "conformité des pompes à carburant. Cette opération vise à garantir l'exactitude des volumes "
                    "délivrés aux consommateurs et s'inscrit dans les missions de métrologie légale confiées au "
                    "laboratoire.\n\n"
                    "Chaque pompe contrôlée fait l'objet d'un étalonnage sur banc de mesure certifié ; en cas d'écart "
                    "constaté au-delà des tolérances réglementaires, l'exploitant dispose d'un délai pour procéder "
                    "aux corrections nécessaires avant une nouvelle vérification. Un poinçon de conformité est "
                    "apposé sur les instruments validés.\n\n"
                    "Cette campagne, menée en collaboration avec les directions régionales du Commerce, couvre "
                    "progressivement l'ensemble des districts du pays et sera reconduite annuellement."
                ),
                category="EVENEMENT",
                is_featured=True,
                days_ago=10,
                image_file="metrologie-carburant.png",
            ),
            dict(
                title="Nouveau partenariat pour l'accréditation ISO/IEC 17025 des laboratoires",
                excerpt="Le LANEMA engage un partenariat technique pour étendre l'accréditation ISO/IEC 17025 à de nouveaux domaines d'analyses.",
                content=(
                    "Afin de renforcer la reconnaissance internationale de ses résultats d'essais, le LANEMA a engagé "
                    "un partenariat technique visant à étendre son accréditation ISO/IEC 17025 à de nouveaux domaines "
                    "d'analyses chimiques et environnementales, facilitant ainsi les exportations des entreprises "
                    "ivoiriennes.\n\n"
                    "L'accréditation ISO/IEC 17025 atteste de la compétence technique d'un laboratoire et de la "
                    "fiabilité de ses résultats d'essais et d'étalonnages. Elle est reconnue par les organismes "
                    "d'accréditation internationaux, ce qui facilite l'acceptation des rapports du LANEMA par les "
                    "partenaires commerciaux à l'étranger.\n\n"
                    "Le partenariat prévoit un accompagnement technique, des audits blancs et la formation du "
                    "personnel des laboratoires concernés sur une période de dix-huit mois."
                ),
                category="PARTENARIAT",
                is_featured=False,
                days_ago=20,
                image_file="accreditation-iso.png",
            ),
            dict(
                title="Journée portes ouvertes au siège du LANEMA à Abobo",
                excerpt="Le LANEMA a organisé une journée portes ouvertes pour présenter ses missions et ses laboratoires aux entreprises et étudiants.",
                content=(
                    "Le laboratoire national a ouvert ses portes aux entreprises, étudiants et administrations afin "
                    "de présenter l'ensemble de ses missions : métrologie, analyses chimiques, microbiologiques, "
                    "environnementales et essais techniques. L'événement a permis de mieux faire connaître le rôle du "
                    "LANEMA dans la protection des consommateurs et la compétitivité des entreprises ivoiriennes.\n\n"
                    "Les visiteurs ont pu suivre des démonstrations en direct dans plusieurs laboratoires, échanger "
                    "avec les techniciens et responsables qualité, et découvrir le parcours complet d'un échantillon, "
                    "du dépôt jusqu'à la remise du rapport d'analyse.\n\n"
                    "Plusieurs étudiants en sciences et en génie industriel ont également profité de la journée pour "
                    "s'informer sur les stages et opportunités de formation proposés par l'établissement."
                ),
                category="EVENEMENT",
                is_featured=False,
                days_ago=45,
                image_file="portes-ouvertes.png",
            ),
        ]

        for a in articles:
            days_ago = a.pop("days_ago")
            image_file = a.pop("image_file")
            obj, created = NewsArticle.objects.get_or_create(
                title=a["title"],
                defaults={
                    **a,
                    "published_at": timezone.now() - timedelta(days=days_ago),
                },
            )
            if not created:
                for field, value in a.items():
                    setattr(obj, field, value)

            image_path = os.path.join(SEED_ASSETS_DIR, image_file)
            if not obj.image and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    obj.image.save(f"{obj.slug}.png", File(f), save=False)

            obj.save()

            if created:
                self.stdout.write(f"  + Actualité créée : {obj.title}")
            else:
                self.stdout.write(f"  ~ Actualité mise à jour : {obj.title}")

    def seed_faq(self):
        faqs = [
            dict(
                category="Demande de devis",
                question="Comment faire une demande de devis auprès du LANEMA ?",
                answer=(
                    "Vous pouvez déposer une demande de devis directement depuis le portail Lab Manager, rubrique "
                    "« Demande de devis ». Décrivez les analyses souhaitées et vos coordonnées ; notre équipe vous "
                    "recontacte avec une proposition détaillée."
                ),
                order=1,
            ),
            dict(
                category="Demande de devis",
                question="Quels documents fournir avec ma demande d'analyse ?",
                answer=(
                    "En général : une description de l'échantillon, la norme ou le référentiel visé (si connu), et "
                    "vos coordonnées de facturation. Des documents complémentaires peuvent être demandés selon le "
                    "type d'analyse."
                ),
                order=2,
            ),
            dict(
                category="Métrologie",
                question="Le LANEMA vérifie-t-il les balances et instruments de mesure des commerçants ?",
                answer=(
                    "Oui. Le LANEMA assure la métrologie légale : vérification des balances, ponts-bascules, pompes "
                    "à carburant, thermomètres, manomètres et compteurs, conformément à la réglementation ivoirienne."
                ),
                order=1,
            ),
            dict(
                category="Analyses",
                question="Quels types de produits peuvent être analysés par le LANEMA ?",
                answer=(
                    "Le LANEMA analyse les produits alimentaires, boissons, produits pétroliers, sols, produits "
                    "chimiques, métaux, eaux usées, eaux potables et minérales, produits laitiers, viandes et "
                    "conserves, entre autres."
                ),
                order=1,
            ),
            dict(
                category="Analyses",
                question="Combien de temps prend une analyse ?",
                answer=(
                    "Le délai dépend du type d'analyse et du domaine concerné (chimique, microbiologique, "
                    "métrologique...). Un délai indicatif est communiqué avec le devis avant validation."
                ),
                order=2,
            ),
            dict(
                category="Contact",
                question="Où se situe le siège du LANEMA ?",
                answer=(
                    "Le siège est situé à Abobo, entre la SONITRA et l'Université Nangui Abrogoua, BP V 174 Abidjan."
                ),
                order=1,
            ),
            dict(
                category="Contact",
                question="Comment contacter le LANEMA ?",
                answer=(
                    "Par téléphone au (+225) 27 22 47 16 00 / (+225) 27 22 47 03 36, ou par email à "
                    "infoline@lanema.ci."
                ),
                order=2,
            ),
        ]

        for f in faqs:
            obj, created = FAQ.objects.get_or_create(
                question=f["question"],
                defaults=f,
            )
            if created:
                self.stdout.write(f"  + FAQ créée : {obj.question}")

    def seed_ai_responses(self):
        responses = [
            dict(
                keyword="devis, demande de devis, tarif, prix, cout",
                question_example="Comment obtenir un devis pour une analyse ?",
                response=(
                    "Pour obtenir un devis, connectez-vous au portail Lab Manager et déposez une demande depuis la "
                    "rubrique « Demande de devis ». Vous pouvez aussi consulter la page « Comment faire une demande "
                    "de devis » de ce site."
                ),
                priority=1,
            ),
            dict(
                keyword="metrologie, balance, pont-bascule, pompe, compteur, etalonnage",
                question_example="Faites-vous la vérification des balances ?",
                response=(
                    "Oui, le LANEMA assure la métrologie légale et industrielle : étalonnage et vérification des "
                    "balances, ponts-bascules, pompes à carburant, thermomètres, manomètres et compteurs."
                ),
                priority=2,
            ),
            dict(
                keyword="analyse chimique, produit chimique, eau, sol, petrolier",
                question_example="Faites-vous des analyses chimiques de l'eau ?",
                response=(
                    "Oui, nos laboratoires réalisent des analyses chimiques sur les produits alimentaires, boissons, "
                    "produits pétroliers, sols, produits chimiques, métaux et eaux usées."
                ),
                priority=3,
            ),
            dict(
                keyword="microbiologie, bacterie, contamination, eau potable, produit laitier",
                question_example="Analysez-vous la qualité microbiologique de l'eau potable ?",
                response=(
                    "Oui, le LANEMA réalise des analyses microbiologiques sur l'eau potable, l'eau minérale, les "
                    "produits alimentaires, laitiers, les viandes et les conserves."
                ),
                priority=4,
            ),
            dict(
                keyword="accreditation, iso 17025, certification",
                question_example="Le LANEMA est-il accrédité ISO 17025 ?",
                response=(
                    "Le LANEMA dispose de plusieurs laboratoires accrédités (analyses chimiques, environnementales, "
                    "microbiologie, métrologie) conformément aux exigences ISO/IEC 17025."
                ),
                priority=5,
            ),
            dict(
                keyword="contact, adresse, telephone, email, horaire, localisation",
                question_example="Comment vous contacter ?",
                response=(
                    "Le siège du LANEMA est situé à Abobo (BP V 174 Abidjan). Téléphone : (+225) 27 22 47 16 00 / "
                    "27 22 47 03 36 — Email : infoline@lanema.ci."
                ),
                priority=6,
            ),
            dict(
                keyword="lab manager, portail, connexion, compte",
                question_example="Comment accéder au portail Lab Manager ?",
                response=(
                    "Le portail Lab Manager permet de suivre vos échantillons, résultats et factures. Cliquez sur "
                    "« Accéder à Lab Manager » en haut de la page pour vous connecter ou créer un compte."
                ),
                priority=7,
            ),
            dict(
                keyword="default",
                question_example="",
                response=(
                    "Merci pour votre question. Un conseiller LANEMA vous répondra bientôt. Vous pouvez aussi nous "
                    "contacter directement via la page Contact ou consulter notre FAQ."
                ),
                priority=99,
            ),
        ]

        for r in responses:
            obj, created = AIKeywordResponse.objects.get_or_create(
                keyword=r["keyword"],
                defaults=r,
            )
            if created:
                self.stdout.write(f"  + Réponse IA créée : {obj.keyword}")
