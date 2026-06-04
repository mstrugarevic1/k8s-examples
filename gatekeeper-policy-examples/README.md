# OPA Gatekeeper Primeri za Kubernetes

Ovaj repozitorijum sadrži praktične primere OPA Gatekeeper polisa za Kubernetes. Cilj je edukacija i demonstracija kako se koriste ConstraintTemplate i Constraint resursi za nametanje sigurnosnih i operativnih pravila.

## Zahtevi

- Kubernetes klaster
- OPA Gatekeeper instaliran na klasteru

### Instalacija Gatekeeper-a

Ako već nemate instaliran Gatekeeper, možete ga instalirati komandom:

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml
```

## Struktura projekta

- `policies/`: Sadrži ConstraintTemplate i Constraint definicije.
- `examples/good/`: Primeri manifesta koji ispunjavaju polise.
- `examples/bad/`: Primeri manifesta koji krše polise (služe za testiranje).

## Polise u ovom repozitorijumu

1. **Namespace owner label**: Svaki Namespace mora imati `owner` labelu.
2. **No privileged containers**: Podovi ne smeju koristiti privilegovane kontejnere.
3. **Approved registries**: Podovi smeju koristiti slike samo iz dozvoljenih registry-ja (npr. `gcr.io`).
4. **Resource requests**: Svi kontejneri moraju imati definisane CPU i memory request-ove.
5. **No LoadBalancer in dev/staging**: LoadBalancer tip servisa je zabranjen u `dev` i `staging` namespace-ovima.
6. **No hostPath volumes**: Podovi ne smeju koristiti `hostPath` volumene.

## Korišćenje

### Primena polisa

Da biste primenili sve polise na vaš klaster, pokrenite:

```bash
make apply
```

### Testiranje polisa

Za testiranje ispravnih manifesta (treba da prođu):

```bash
make test-good
```

Za testiranje neispravnih manifesta (treba da budu odbijeni):

```bash
make test-bad
```

### Čišćenje

Da biste uklonili sve resurse kreirane ovim primerima:

```bash
make clean
```

## Objašnjenje polisa

Svaka polisa se sastoji iz dva dela:
1. **ConstraintTemplate**: Definiše Rego logiku i parametre polise.
2. **Constraint**: Primena polise na konkretne resurse (npr. samo na Podove ili određene namespace-ove).
