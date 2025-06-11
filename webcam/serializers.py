from django.contrib.auth.models import User
from rest_framework import serializers, validators
from webcam.models import UserProfileModel

class RegisterSerializer(serializers.ModelSerializer):
    # Ensure the email is unique
    email = serializers.EmailField(
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )
    # Ensure the username is unique
    username = serializers.CharField(
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        # Fields to expect in the registration request
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def create(self, validated_data):
        # Create the user, making sure to hash the password correctly
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ""),
            last_name=validated_data.get('last_name', "")
        )
        # Use set_password to handle hashing
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfileModel.
    """
    class Meta:
        model = UserProfileModel
        # List the fields from your UserProfileModel that you want to return
        fields = ('city', 'country', 'county_or_state', 'phone')


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the built-in User model that includes nested profile data.
    """
    # This nests the UserProfileSerializer. The 'profile' name comes from the
    # related_name we set on the OneToOneField in models.py.
    profile = UserProfileSerializer()

    class Meta:
        model = User
        # List the fields from the built-in User model you want to return
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')

    def update(self, instance, validated_data):
        #TODO: Investigate here why profile data gets ignored
        profile_data = validated_data.pop('profile', {})
        print(profile_data)

        profile_instance = instance.profile

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile_instance, attr, value)

        instance.save()
        profile_instance.save()

        return instance