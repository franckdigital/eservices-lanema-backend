from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, DeviceLock
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class DeviceLockSerializer(serializers.ModelSerializer):
    """Serializer pour les verrouillages d'appareils"""
    class Meta:
        model = DeviceLock
        fields = ['id', 'device_id', 'user', 'username', 'email', 'locked_at', 'last_used']
        read_only_fields = ['id', 'locked_at', 'last_used']


class DeviceLockViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour lister les appareils verrouillés (admin uniquement)"""
    queryset = DeviceLock.objects.all().order_by('-last_used')
    serializer_class = DeviceLockSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        # Vérifier que l'utilisateur est admin
        try:
            profile = self.request.user.profile
            if profile.role not in ['ADMIN', 'superadmin']:
                return DeviceLock.objects.none()
        except:
            return DeviceLock.objects.none()
        
        return DeviceLock.objects.all().order_by('-last_used')


class CheckDeviceLockView(APIView):
    """Vérifier si un appareil est verrouillé pour un autre utilisateur"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        username = request.data.get('username')
        
        if not device_id or not username:
            return Response({
                'error': 'device_id et username requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier si l'appareil est verrouillé
            device_lock = DeviceLock.objects.filter(device_id=device_id).first()
            
            if device_lock:
                # L'appareil est verrouillé
                if device_lock.username != username:
                    # Verrouillé pour un autre utilisateur
                    return Response({
                        'is_locked': True,
                        'locked_by': device_lock.username,
                        'message': f'Ce téléphone est associé à {device_lock.username}. Contactez l\'administrateur.'
                    })
                else:
                    # Verrouillé pour le même utilisateur
                    device_lock.last_used = timezone.now()
                    device_lock.save()
                    return Response({
                        'is_locked': False,
                        'message': 'Appareil autorisé'
                    })
            else:
                # Nouvel appareil pour ce compte : interdire les connexions
                # simultanees sur plusieurs telephones. On identifie l'autre
                # session via request.user (authentifie par JWT), plus fiable
                # que le champ username soumis par le client.
                other_lock = DeviceLock.objects.filter(user=request.user).exclude(device_id=device_id).first()
                if other_lock:
                    return Response({
                        'is_locked': True,
                        'locked_by': username,
                        'message': "Ce compte est déjà connecté sur un autre téléphone. Déconnectez-vous d'abord sur l'autre appareil, ou contactez l'administrateur pour le libérer."
                    })
                # Appareil non verrouillé
                return Response({
                    'is_locked': False,
                    'message': 'Appareil non verrouillé'
                })
                
        except Exception as e:
            logger.error(f'Erreur vérification verrouillage: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LockDeviceView(APIView):
    """Verrouiller un appareil pour l'utilisateur actuel"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        username = request.data.get('username')
        email = request.data.get('email')
        
        if not device_id or not username:
            return Response({
                'error': 'device_id et username requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier si l'appareil est déjà verrouillé
            device_lock = DeviceLock.objects.filter(device_id=device_id).first()
            
            if device_lock:
                if device_lock.username != username:
                    # Verrouillé pour un autre utilisateur
                    return Response({
                        'error': f'Appareil déjà verrouillé pour {device_lock.username}'
                    }, status=status.HTTP_403_FORBIDDEN)
                else:
                    # Mettre à jour la dernière utilisation
                    device_lock.last_used = timezone.now()
                    device_lock.save()
                    return Response({
                        'message': 'Appareil déjà verrouillé pour vous'
                    })
            else:
                # Refuser la creation d'un nouveau verrouillage si ce compte a
                # deja une session active sur un autre appareil (memes regles
                # que CheckDeviceLockView, au cas ou cet endpoint serait
                # appele sans passer par la verification prealable).
                other_lock = DeviceLock.objects.filter(user=request.user).exclude(device_id=device_id).first()
                if other_lock:
                    return Response({
                        'error': "Ce compte est déjà connecté sur un autre téléphone. Contactez l'administrateur pour le libérer avant de vous connecter sur ce nouvel appareil."
                    }, status=status.HTTP_403_FORBIDDEN)

                # Créer un nouveau verrouillage
                device_lock = DeviceLock.objects.create(
                    device_id=device_id,
                    user=request.user,
                    username=username,
                    email=email or request.user.email
                )
                
                logger.info(f'Appareil {device_id} verrouillé pour {username}')
                
                return Response({
                    'message': 'Appareil verrouillé avec succès',
                    'device_id': device_id,
                    'username': username
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f'Erreur verrouillage appareil: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnlockDeviceView(APIView):
    """Déverrouiller un appareil : un administrateur peut déverrouiller
    n'importe quel appareil ; un utilisateur normal ne peut déverrouiller que
    l'appareil actuellement verrouillé pour SON PROPRE compte (utilisé à la
    déconnexion, pour libérer le verrou sans intervention d'un administrateur
    et permettre une connexion sur un autre téléphone)."""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        device_id = request.data.get('device_id')

        if not device_id:
            return Response({
                'error': 'device_id requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        is_admin = False
        try:
            is_admin = request.user.profile.role in ['ADMIN', 'superadmin']
        except Exception:
            is_admin = False

        try:
            device_lock = DeviceLock.objects.filter(device_id=device_id).first()

            if not device_lock:
                return Response({
                    'message': 'Appareil non verrouillé'
                })

            if not is_admin and device_lock.user_id != request.user.id:
                return Response({
                    'error': "Vous ne pouvez déverrouiller que l'appareil verrouillé pour votre propre compte."
                }, status=status.HTTP_403_FORBIDDEN)

            username = device_lock.username
            device_lock.delete()
            logger.info(f'Appareil {device_id} déverrouillé par {request.user.username}')

            return Response({
                'message': f'Appareil déverrouillé (était verrouillé pour {username})'
            })
                
        except Exception as e:
            logger.error(f'Erreur déverrouillage appareil: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
