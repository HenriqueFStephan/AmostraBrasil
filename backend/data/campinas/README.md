# Dados de áreas verdes – Campinas

O arquivo `areas_verdes.geojson` contém polígonos de parques, bosques e mata para o município de Campinas, usados como camada extra no mapa quando o usuário seleciona Campinas.

**Conteúdo atual:** geometrias aproximadas (Parque Portugal/Lagoa do Taquaral, Bosque dos Jequitibás, Mata Santa Genebra) para demonstração.

**Dados oficiais:** A Prefeitura de Campinas disponibiliza metadados e exportação de shapefiles em:

- [Metadados geoespaciais – Campinas](https://www.campinas.sp.gov.br/sites/metadadosgeoespaciais/descricao)
- Portal informacao-didc (ex.: Vegetação Natural, Parques Lineares) e portal geoambiental

Para substituir por dados oficiais: baixe os shapefiles, converta para GeoJSON (ex.: QGIS ou `ogr2ogr -f GeoJSON areas_verdes.geojson arquivo.shp`) e coloque aqui, mantendo propriedades como `nome` e `tipo` (parque, bosque, mata, lago) para estilização e popup no mapa.
