# Analyysi ennakkotehtävästä

# 1. Mitä tekoäly teki hyvin?
Tekoäly onnistui hyvin hahmottamaan tehtävän kokonaisuuden, tuottamaan raa'an perusrakenteen kokoushuoneiden varausrajapinnalle ja valitsi tarkoituksenmukaisen teknologian (FastAPI). Perustoiminnot, kuten varauksen luonti, poisto, muokkaus ja listaaminen, olivat loogisesti toteutettuja ja vastasivat tehtävän “must have” -vaatimuksia.
Lisäksi tekoäly osasi mallintaa toimintalogiikan oikein: päällekkäisten varausten estäminen, aikojen validointi sekä varauksen enimmäiskeston tarkistaminen. Myös virheilmoitukset olivat selkeitä ja käyttäjälle ymmärrettäviä, mikä parantaa rajapinnan käytettävyyttä.
Tekoäly myös ehdotti järkeviä laajennuksia “should have” ja “could have” -tasolle, kuten käyttäjäkohtaisia näkymiä, huonelistausta ja mahdollisia jatkokehityskohteita (autentikointi, roolit, toistuvat varaukset). Kun API:n testauksessa todettiin koodissa olevan virheitä, tekoäly osasi antaa korjausohjeet näille virheille hyvin, eikä tehtävän kannalta hyvän lopputuloksen saavuttaminen vaatinut suuria määriä committeja ja korjaustoimenpiteitä. 

# 2. Mitä tekoäly teki huonosti?
Vaikka tekoäly tuotti toimivan perusratkaisun, koodissa ilmeni useita ongelmia, jotka paljastuivat vasta käytännön testauksessa. Merkittävin puute oli se, että alkuperäinen ratkaisu käytti suoraan globaaleja sanakirjoja (dict) ilman selkeää abstraktiokerrosta. Tämä teki ratkaisusta enemmän skriptimäisen kuin oikean backend-sovelluksen ja vaikeutti arkkitehtuurin ymmärtämistä.
Lisäksi tekoäly teki virheen aikakäsittelyssä: se vertasi keskenään timezone-naive ja timezone-aware datetime-funktioita, mikä johti 500 Internal Server Error -virheeseen. Tämä on tyypillinen, mutta vakava virhe ja osoittaa, ettei tekoäly aina huomioi kaikkia koodin yksityiskohtia.
Tekoäly ei myöskään aluksi ohjannut systemaattiseen testaamiseen ja koodiin liittyneet ongelmat havaittiin vasta Swagger-rajapinnan kautta manuaalisissä testeissä. 

# 3. Tärkeimmät parannukset ja miksi ne olivat tärkeitä
Tärkein parannus oli in-memory-tietokannan toteuttaminen erillisen InMemoryDB-luokan avulla. Tämä muutos oli merkittävä, koska se toi sovellukseen selkeän tietokerroksen ja erotti liiketoimintalogiikan varsinaisesta datan tallennuksesta.
Tämän ansiosta:
API:ta pystyttiin testaamaan kokonaisuutena ilman ulkoisia riippuvuuksia.
Koodi muistutti enemmän oikeaa backend-arkkitehtuuria.
Ratkaisu on helposti laajennettavissa oikeaan tietokantaan (esim. PostgreSQL) ilman, että endpointteja tarvitsee muuttaa. 


Toinen keskeinen parannus oli aikakäsittelyn korjaus (timezone), tarkemmin sanottuna datetime.utcnow()-kutsun korvaaminen datetime.now(timezone.utc)-kutsulla. Tämä poisti 500-virheen ja varmisti, että API käsittelee aikoja oikein.
Tämä parannus oli tärkeä, koska se muutti sovelluksen toimimattomasta luotettavaksi ja sujuvasti toimivaksi. Kyseinen ohjelmointivirhe virhe esti koko järjestelmän toiminnan.

Lisäksi koodiin tehtiin useita pienempiä mutta tärkeitä parannuksia:
Kaikki tietoon liittyvät operaatiot kulkevat yhden rajapinnan (DB-luokan) kautta.
Virhetilanteet palauttavat hallittuja HTTP-virheitä 400/404/409 -koodeilla.
API:ta voitiin testata järjestelmällisesti Swaggerilla ja kaikki toiminnot todettiin toimiviksi.

Parannuksista on mielestäni myös merkittävää mainita, miksi joitain jätettiin tekemättä. Päätin tietoisesti jättää esimerkiksi refakturoinnin tekemättä, koska API:n koodi oli suhteellisen lyhyt, enkä koe, että siitä olisi tässä tehtävässä merkittävää hyötyä koodin selkeyteen tai API:n toimivuuteen tai luotettavuuteen. Tämä olisi kumminkin jatkokehityksessä erittäin hyvä askel, kun ominaisuuksia ja toimintoja lisättäisiin enemmän.

# Yhteenveto
Tekoäly tuotti jopa yllättävän nopeasti tehtävän scopeen perusratkaisun, joka vastasi vaatimuksia. Alkuperäinen raakaversio sisälsi kuitenkin muutamia pieniä, mutta toimivuuden kannalta merkittäviä virheitä, jotka korjaamalla rajapinnasta saatiin luotettava, järjestelmällisesti testattava ja myös helposti jatkokehitettävä. Merkittävimpiä parannuksia tekolyn tuottavaan raakaversioon oli erityisesti in-memory-tietokannan käyttöönotto, mikä nosti koodin ja itse API:n tasoa merkittävästi. 
