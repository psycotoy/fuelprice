from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET
from pyproj import Proj, Transformer

app = Flask(__name__)

# 좌표계 설정
WGS84 = {'proj': 'latlong', 'datum': 'WGS84', 'ellps': 'WGS84'}
KATEC = {'proj': 'tmerc', 'lat_0': '38N', 'lon_0': '128E', 'ellps': 'bessel',
         'x_0': '400000', 'y_0': '600000', 'k': '0.9999', 'a': '6377397.155',
         'b': '6356078.9628181886', 'towgs84': '-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43', 'units': 'm'}

inProj = Proj(**WGS84)
outProj = Proj(**KATEC)

# 기본 주유소 URL 목록 (11개)
urls = [
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0018249&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0018144&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0022751&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0032967&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0033287&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0017743&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0022718&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0033731&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0017724&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0018227&out=xml",
    "https://www.opinet.co.kr/api/detailById.do?code=F241112439&id=A0018246&out=xml"
]

@app.route('/')
def index():
    gas_stations = []
    min_prices = {"고급휘발유": float('inf'), "휘발유": float('inf'), "경유": float('inf')}

    for url in urls:
        response = requests.get(url)
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()

        for oil in root.findall('OIL'):
            station_info = {
                "name": oil.find('OS_NM').text,
                "address": oil.find('VAN_ADR').text,
                "brand_code": oil.find('POLL_DIV_CO').text,
                "prices": []
            }
            for price_info in oil.findall('OIL_PRICE'):
                prod_code = price_info.find('PRODCD').text
                price = int(price_info.find('PRICE').text)
                
                # 유종 타입 설정
                if prod_code == 'B034':  # 고급휘발유
                    fuel_type = "고급휘발유"
                elif prod_code == 'B027':  # 보통휘발유
                    fuel_type = "휘발유"
                elif prod_code == 'D047':  # 자동차경유
                    fuel_type = "경유"
                else:
                    fuel_type = None
                
                # fuel_type이 None이 아닌 경우에만 추가
                if fuel_type:
                    # 유종별 최저가 업데이트
                    if price < min_prices[fuel_type]:
                        min_prices[fuel_type] = price

                    # 유종 데이터 추가
                    station_info["prices"].append({
                        "prod_code": prod_code,
                        "price": price,
                        "fuel_type": fuel_type,
                        "trade_date": price_info.find('TRADE_DT').text,
                        "trade_time": price_info.find('TRADE_TM').text
                    })
            gas_stations.append(station_info)

    return render_template('index.html', gas_stations=gas_stations, min_prices=min_prices)

# 반경 3km 내 주유소 정보, 기본 서울시청 좌표
@app.route('/near')
def near():
    longitude = float(request.args.get("x", 126.9778))
    latitude = float(request.args.get("y", 37.5664))
    radius = 3000 #최대5000(5km)
    prodcd = request.args.get("fuelType", "B027")

    # 좌표 변환
    transformer = Transformer.from_proj(inProj, outProj)
    katec_x, katec_y = transformer.transform(longitude, latitude)

    # API 요청 URL 생성
    url = f"http://www.opinet.co.kr/api/aroundAll.do?code=F241112439&x={katec_x}&y={katec_y}&radius={radius}&sort=1&prodcd={prodcd}&out=xml"
    
    response = requests.get(url)
    print("API 요청 URL:", url)
    print("API 응답 상태 코드:", response.status_code)
    print("API 응답 내용:", response.text)

    near_stations = []
    if response.status_code == 200:
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()

        for oil in root.findall('OIL'):
            name = oil.find('OS_NM').text if oil.find('OS_NM') is not None else "정보 없음"
            brand_code = oil.find('POLL_DIV_CO').text if oil.find('POLL_DIV_CO') is not None else "브랜드 없음"
            price = int(oil.find('PRICE').text) if oil.find('PRICE') is not None else None
            distance_km = float(oil.find('DISTANCE').text) / 1000 if oil.find('DISTANCE') is not None else None
            
            station_info = {
                "name": name,
                "brand_code": brand_code,
                "price": price,
                "distance_km": distance_km
            }
            near_stations.append(station_info)
    
    print("수집된 주유소 데이터:", near_stations)
    return render_template('near.html', gas_stations=near_stations, selected_fuel=prodcd)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=51234)
