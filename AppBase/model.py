# -*- coding: utf-8 -*-


from django.db import models
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.utils import timezone


class AppBaseModelQuerySet(models.QuerySet):

    def A(self):
        return self.filter(trashed__exact=False)

    def i(self, n):
        try:
            return self.get(id__exact=n, trashed__exact=False)
        except:
            return False

    def ai(self, n):
        try:
            return self.get(id__exact=n)
        except:
            return False

    def k(self, key):
        try:
            return self.get(key__exact=key, trashed__exact=False)
        except:
            return False

    def ki(self, key):
        try:
            return self.get(key__exact=key)
        except:
            return False

    def f(self, **kwargs):
        kwargs["trashed__exact"] = False
        return self.filter(**kwargs)

    def af(self, **kwargs):
        return self.filter(**kwargs)

    def g(self, **kwargs):
        kwargs["trashed__exact"] = False
        res = self.filter(**kwargs)
        if res.count() == 0:
            return False
        return res[0]

    def ag(self, **kwargs):
        res = self.filter(**kwargs)
        if res.count() == 0:
            return False
        return res[0]

    def f_or(self, **kwargs):
        logic = Q(id__exact=-121231)
        for k, v in kwargs.items():
            logic = logic | Q(**{k: v})
        logic = logic & Q(trashed__exact=False)

        return self.filter(logic)

    def af_or(self, **kwargs):
        logic = Q(id__exact=-121231)
        for k, v in kwargs.items():
            logic = logic | Q(**{k: v})

        return self.filter(logic)


class AppBaseModelManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return AppBaseModelQuerySet(self.model, using=self._db)

    def A(self):
        return self.get_queryset().A()

    def all(self):
        return self.get_queryset().all()

    def i(self, n):
        return self.get_queryset().i(n)

    def ai(self, n):
        return self.get_queryset().ai(n)

    def k(self, key):
        return self.get_queryset().k(key)

    def ki(self, key):
        return self.get_queryset().ki(key)

    def f(self, **kwargs):
        return self.get_queryset().f(**kwargs)

    def af(self, **kwargs):
        return self.get_queryset().af(**kwargs)

    def g(self, **kwargs):
        return self.get_queryset().g(**kwargs)

    def ag(self, **kwargs):
        return self.get_queryset().ag(**kwargs)

    def f_or(self, **kwargs):
        return self.get_queryset().f_or(**kwargs)

    def af_or(self, **kwargs):
        return self.get_queryset().af_or(**kwargs)


class AppBaseModel(models.Model):
    trashed = models.BooleanField(default=False)
    update = models.DateTimeField(default=timezone.now)
    create = models.DateTimeField(default=timezone.now)

    objects = AppBaseModelManager()

    class Meta:
        abstract = True
        base_manager_name = 'objects'

    def save(self, *args, **kwargs):
        self.update = timezone.now()
        if not self.pk:  # new record
            self.create = timezone.now()
        super(AppBaseModel, self).save(*args, **kwargs)

    @classmethod
    def genkey(cls, maxl, startletter="", field="key__exact"):
        try:
            l = 1
            last_id = cls.objects.latest('id')
            x62 = 62  # Number of Uppercase and Lowercase alphabets and 0-9
            while True:
                if last_id.id < x62 * 0.8:
                    break
                l += 1
                x62 *= 62
        except:
            l = 1


        startletter_len = len(startletter)

        if l > maxl - startletter_len:
            l = maxl - startletter_len

        while True:
            key = startletter + get_random_string(length=l)
            filters = {field: key}

            if cls.objects.filter(**filters).count() == 0:
                return key

    @classmethod
    def genfixedkey(cls, l, startletter="", field="key__exact"):
        startletter_len = len(startletter)
        if startletter_len > 0:
            l = l - startletter_len

        while True:
            key = startletter + get_random_string(length=l)
            filters = {field: key}

            if cls.objects.filter(**filters).count() == 0:
                return key

    # def __unicode__(self):
    # 	return self.T(self)

    # usable as ModelName.A()
    @classmethod
    def A(cls, **kwargs):
        return cls.objects.A()

    # usable as ModelName.D()
    @classmethod
    def all(cls):
        return cls.objects.all()

    # usable as ModelName.i(1)
    @classmethod
    def i(cls, n):
        return cls.objects.i(n)

    # usable as ModelName.ai(1)
    @classmethod
    def ai(cls, n):
        return cls.objects.ai(n)

    # usable as ModelName.k("Qz1")
    @classmethod
    def k(cls, key):
        return cls.objects.k(key)

    # usable as ModelName.ki("Qz1")
    @classmethod
    def ki(cls, key):
        return cls.objects.ki(key)

    # usable as ModelName.trash(1)
    # usable as ModelName.trash([1,2,3,])
    @classmethod
    def trash(cls, n):
        c = cls.objects.i(n)
        c.update(trashed=True)
        return False

    # usable as ModelName.f(Create__gte=now())
    @classmethod
    def f(cls, **kwargs):
        return cls.objects.f(**kwargs)

    # usable as ModelName.f(Create__gte=now())
    @classmethod
    def af(cls, **kwargs):
        return cls.objects.af(**kwargs)

    # usable as ModelName.g(Create__gte=now())
    @classmethod
    def g(cls, **kwargs):
        return cls.objects.g(**kwargs)

    # usable as ModelName.ag(Create__gte=now())
    @classmethod
    def ag(cls, **kwargs):
        return cls.objects.ag(**kwargs)

    # usable as ModelName.f_or(P1=2, P2=3)
    @classmethod
    def f_or(cls, **kwargs):
        return cls.objects.f_or(**kwargs)

    # usable as ModelName.af_or(P1=2, P2=3)
    @classmethod
    def af_or(cls, **kwargs):
        return cls.objects.af_or(**kwargs)

    # usable as ModelInstances.setTrash()
    def remove(self):
        self.trash = True
        self.save()

    class Meta:
        abstract = True
        base_manager_name = 'objects'
