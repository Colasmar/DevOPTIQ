# Code/routes/vsdx_conection_parser.py
"""
Parseur de connexions VSDX pour l'import des liens entre activités.

Ce module extrait les connexions (flèches) d'un fichier Visio (.vsdx)
et retourne une liste de connexions avec :
- source_shape_id / source_name
- target_shape_id / target_name  
- data_name (nom de la donnée qui transite)
- data_type (déclenchante / nourrissante)

CORRECTIONS:
- v2: Utilisation de itertext() pour récupérer tout le texte
- v3: Exclusion des drapeaux (layer 6) des connexions
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Set
import os


class VsdxConnectionParser:
    """Parse les connexions d'un fichier VSDX."""
    
    VISIO_NS = {'v': 'http://schemas.microsoft.com/office/visio/2012/main'}
    
    # Layers à exclure des connexions (drapeaux, légendes, etc.)
    EXCLUDED_LAYERS = {'6'}  # 6 = Result/Drapeau (représentation visuelle, pas une vraie activité)
    
    # Layers des vraies activités
    ACTIVITY_LAYERS = {'1'}  # 1 = Activity (rectangles)
    
    def __init__(self, vsdx_path: str):
        """
        Initialise le parser avec le chemin du fichier VSDX.
        
        Args:
            vsdx_path: Chemin vers le fichier .vsdx
        """
        self.vsdx_path = vsdx_path
        self.shape_info: Dict[str, Dict] = {}
        self.connections: List[Dict] = []
        self.excluded_shape_ids: Set[str] = set()  # Shapes à ignorer (drapeaux)
        
    def parse(self) -> Tuple[List[Dict], List[str]]:
        """
        Parse le fichier VSDX et extrait les connexions.
        
        Returns:
            Tuple contenant:
            - Liste des connexions
            - Liste des erreurs/warnings
        """
        errors = []
        
        # Vérifier que le fichier existe
        if not os.path.exists(self.vsdx_path):
            return [], [f"Fichier non trouvé: {self.vsdx_path}"]
        
        # Vérifier l'extension
        if not self.vsdx_path.lower().endswith('.vsdx'):
            return [], ["Le fichier doit être au format .vsdx"]
        
        try:
            # Extraire et parser le fichier page1.xml
            with zipfile.ZipFile(self.vsdx_path, 'r') as zf:
                # Lister les fichiers de pages disponibles
                page_files = [f for f in zf.namelist() if 'pages/page' in f and f.endswith('.xml')]
                
                if not page_files:
                    return [], ["Aucune page trouvée dans le fichier VSDX"]
                
                # Parser la première page (ou toutes si plusieurs)
                for page_file in page_files:
                    page_xml = zf.read(page_file)
                    self._parse_page(page_xml, errors)
                    
        except zipfile.BadZipFile:
            return [], ["Le fichier VSDX est corrompu ou invalide"]
        except Exception as e:
            return [], [f"Erreur lors du parsing: {str(e)}"]
        
        return self.connections, errors
    
    def _parse_page(self, page_xml: bytes, errors: List[str]):
        """Parse une page XML et extrait les shapes et connexions."""
        
        try:
            root = ET.fromstring(page_xml)
        except ET.ParseError as e:
            errors.append(f"Erreur parsing XML: {str(e)}")
            return
        
        # 1) Récupérer tous les shapes avec leurs infos ET identifier les drapeaux
        shapes = root.findall('.//v:Shape', self.VISIO_NS)
        
        for shape in shapes:
            shape_id = shape.get('ID')
            if not shape_id:
                continue
                
            shape_name = shape.get('Name', '')
            
            # Récupérer le layer du shape
            layer_cell = shape.find(".//v:Cell[@N='LayerMember']", self.VISIO_NS)
            layer = layer_cell.get('V') if layer_cell is not None else None
            
            # Marquer les shapes à exclure (drapeaux layer 6)
            if layer in self.EXCLUDED_LAYERS:
                self.excluded_shape_ids.add(shape_id)
            
            # Récupérer le texte avec itertext()
            text_elem = shape.find('.//v:Text', self.VISIO_NS)
            text = ''
            if text_elem is not None:
                text = ''.join(text_elem.itertext()).strip()
                text = ' '.join(text.split())
            
            self.shape_info[shape_id] = {
                'name': shape_name,
                'text': text,
                'layer': layer
            }
        
        # 2) Récupérer toutes les connexions
        connects = root.findall('.//v:Connect', self.VISIO_NS)
        connectors: Dict[str, Dict] = {}
        
        for connect in connects:
            from_sheet = connect.get('FromSheet')
            from_cell = connect.get('FromCell', '')
            to_sheet = connect.get('ToSheet')
            
            if not from_sheet or not to_sheet:
                continue
            
            if from_sheet not in connectors:
                connectors[from_sheet] = {'source': None, 'target': None}
            
            # BeginX = début du connecteur (source)
            # EndX = fin du connecteur (cible)
            if 'BeginX' in from_cell:
                connectors[from_sheet]['source'] = to_sheet
            elif 'EndX' in from_cell:
                connectors[from_sheet]['target'] = to_sheet
        
        # 3) Construire la liste des connexions avec noms
        # EN EXCLUANT les connexions vers/depuis des drapeaux (layer 6)
        for conn_id, data in connectors.items():
            source_id = data.get('source')
            target_id = data.get('target')
            
            # Ignorer les connexions incomplètes
            if not source_id or not target_id:
                continue
            
            # *** NOUVEAU: Ignorer les connexions impliquant des drapeaux ***
            if source_id in self.excluded_shape_ids or target_id in self.excluded_shape_ids:
                continue
            
            source_info = self.shape_info.get(source_id, {})
            target_info = self.shape_info.get(target_id, {})
            conn_info = self.shape_info.get(conn_id, {})
            
            source_name = source_info.get('text') or source_info.get('name', '')
            target_name = target_info.get('text') or target_info.get('name', '')
            
            # Filtrer les shapes sans nom valide
            if not source_name or not target_name:
                continue
            
            # Ignorer les shapes "Résultat" qui sont des artefacts Visio
            if source_name.startswith('Résultat.') or target_name.startswith('Résultat.'):
                continue
            
            # Le nom du connecteur peut être le nom de la donnée qui transite
            connector_text = conn_info.get('text') or ''
            connector_name = conn_info.get('name') or ''
            
            # Extraire le type et le nom de la donnée
            data_type, data_name = self._extract_data_info(connector_name, connector_text)
            
            self.connections.append({
                'source_shape_id': source_id,
                'source_name': source_name.strip(),
                'target_shape_id': target_id,
                'target_name': target_name.strip(),
                'connector_id': conn_id,
                'data_name': data_name,
                'data_type': data_type
            })
    
    def _extract_data_info(self, connector_name: str, connector_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait le type et le nom de la donnée depuis le connecteur.
        
        Convention Visio:
        - "T xxx" ou "T- xxx" = donnée déclenchante
        - "N xxx" ou "N- xxx" = donnée nourrissante
        
        Returns:
            Tuple (data_type, data_name)
        """
        data_type = None
        data_name = connector_text or connector_name or None
        
        # Analyser le préfixe du nom du connecteur
        name = connector_name.strip()
        
        if name.startswith('T ') or name.startswith('T-'):
            data_type = 'déclenchante'
            data_name = name[2:].strip() if len(name) > 2 else connector_text
        elif name.startswith('N ') or name.startswith('N-'):
            data_type = 'nourrissante'
            data_name = name[2:].strip() if len(name) > 2 else connector_text
        
        if data_name and data_name.strip() == '':
            data_name = None
            
        return data_type, data_name
    
    def get_unique_activities(self) -> List[str]:
        """Retourne la liste des noms d'activités uniques trouvées dans les connexions."""
        activities = set()
        for conn in self.connections:
            activities.add(conn['source_name'])
            activities.add(conn['target_name'])
        return sorted(list(activities))
    
    def get_excluded_shapes(self) -> List[Dict]:
        """Retourne les shapes exclus (drapeaux) pour info."""
        return [
            {'shape_id': sid, 'text': self.shape_info.get(sid, {}).get('text', '?')}
            for sid in self.excluded_shape_ids
        ]


def parse_vsdx_connections(vsdx_path: str) -> Tuple[List[Dict], List[str]]:
    """
    Fonction utilitaire pour parser les connexions d'un fichier VSDX.
    """
    parser = VsdxConnectionParser(vsdx_path)
    return parser.parse()


def normalize_activity_name(name: str) -> str:
    """Normalise un nom d'activité pour la comparaison."""
    if not name:
        return ''
    name = name.replace("'", "'").replace("'", "'").replace("`", "'")
    name = ' '.join(name.lower().split())
    return name


def validate_connections_against_activities(
    connections: List[Dict], 
    existing_activities: Dict[str, int]
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Valide les connexions par rapport aux activités existantes.
    Utilise normalize_activity_name() pour une comparaison robuste.
    """
    valid_connections = []
    invalid_connections = []
    missing_activities = set()
    
    # Créer un mapping normalisé
    normalized_activities = {}
    for name, act_id in existing_activities.items():
        norm_name = normalize_activity_name(name)
        normalized_activities[norm_name] = (name, act_id)
    
    for conn in connections:
        source_name = conn['source_name']
        target_name = conn['target_name']
        
        source_norm = normalize_activity_name(source_name)
        target_norm = normalize_activity_name(target_name)
        
        source_match = normalized_activities.get(source_norm)
        target_match = normalized_activities.get(target_norm)
        
        if source_match and target_match:
            conn_with_ids = conn.copy()
            conn_with_ids['source_activity_id'] = source_match[1]
            conn_with_ids['target_activity_id'] = target_match[1]
            valid_connections.append(conn_with_ids)
        else:
            invalid_connections.append(conn)
            if not source_match:
                missing_activities.add(source_name)
            if not target_match:
                missing_activities.add(target_name)
    
    return valid_connections, invalid_connections, sorted(list(missing_activities))


# Test du module
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vsdx_connection_parser.py <fichier.vsdx>")
        sys.exit(1)
    
    vsdx_path = sys.argv[1]
    parser = VsdxConnectionParser(vsdx_path)
    connections, errors = parser.parse()
    
    if errors:
        print("Erreurs:")
        for e in errors:
            print(f"  - {e}")
    
    # Afficher les shapes exclus
    excluded = parser.get_excluded_shapes()
    if excluded:
        print(f"\nShapes exclus (drapeaux): {len(excluded)}")
        for ex in excluded:
            print(f"  - Shape {ex['shape_id']}: {ex['text']}")
    
    print(f"\nConnexions trouvées: {len(connections)}")
    for conn in connections:
        print(f"  {conn['source_name']} → {conn['target_name']}")