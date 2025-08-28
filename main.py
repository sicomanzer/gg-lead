import os
import pandas as pd
from serpapi import GoogleSearch
import streamlit as st
import time
from datetime import datetime
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# API Key สำหรับ SerpApi (ควรเก็บใน .env file)
API_KEY = os.getenv('SERPAPI_KEY', '42ed65c54ab568d1396bbb8f10f5c80376f5e05e801f1ed41697bca017d214f0')

class BusinessSearcher:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def search_businesses(self, query, location="Thailand", num_results=20):
        """
        ค้นหาธุรกิจใน Google Maps
        
        Args:
            query (str): คำค้นหา เช่น "ร้านอาหาร", "โรงแรม", "ร้านกาแฟ"
            location (str): สถานที่ค้นหา
            num_results (int): จำนวนผลลัพธ์ที่ต้องการ
        
        Returns:
            list: รายการข้อมูลธุรกิจ
        """
        businesses = []
        
        try:
            params = {
                "engine": "google_maps",
                "q": query,
                "ll": "@13.7563,100.5018,15z",  # พิกัดกรุงเทพฯ
                "type": "search",
                "api_key": self.api_key,
                "num": num_results
            }
            
            if location and location != "Thailand":
                params["q"] = f"{query} {location}"
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "local_results" in results:
                for result in results["local_results"]:
                    business_data = self.extract_business_info(result)
                    if business_data:
                        businesses.append(business_data)
            
            # หากมีหน้าถัดไป ให้ค้นหาต่อจนครบจำนวนที่ต้องการ
            page_count = 1
            max_pages = 3  # จำกัดจำนวนหน้าเพื่อป้องกัน infinite loop
            
            while ("serpapi_pagination" in results and "next" in results["serpapi_pagination"] 
                   and len(businesses) < num_results and page_count < max_pages):
                
                time.sleep(1)  # หน่วงเวลาเพื่อไม่ให้เกิน rate limit
                
                # ดึง parameters สำหรับหน้าถัดไป
                if "next" in results["serpapi_pagination"]:
                    # สร้าง parameters ใหม่สำหรับหน้าถัดไป
                    next_params = params.copy()
                    if "start" in results["serpapi_pagination"]:
                        next_params["start"] = results["serpapi_pagination"]["start"]
                    next_search = GoogleSearch(next_params)
                    results = next_search.get_dict()
                else:
                    break
                
                if "local_results" in results:
                    for result in results["local_results"]:
                        if len(businesses) >= num_results:
                            break
                        business_data = self.extract_business_info(result)
                        if business_data:
                            businesses.append(business_data)
                
                page_count += 1
            
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}")
        
        return businesses
    
    def extract_business_info(self, result):
        """
        ดึงข้อมูลธุรกิจจากผลลัพธ์
        
        Args:
            result (dict): ข้อมูลผลลัพธ์จาก SerpApi
        
        Returns:
            dict: ข้อมูลธุรกิจที่จัดรูปแบบแล้ว
        """
        try:
            business_info = {
                "ชื่อธุรกิจ": result.get("title", "ไม่ระบุ"),
                "ที่อยู่": result.get("address", "ไม่ระบุ"),
                "เบอร์โทรศัพท์": result.get("phone", "ไม่ระบุ"),
                "เว็บไซต์": result.get("website", "ไม่ระบุ"),
                "ประเภทธุรกิจ": result.get("type", "ไม่ระบุ"),
                "คะแนนรีวิว": result.get("rating", "ไม่ระบุ"),
                "จำนวนรีวิว": result.get("reviews", "ไม่ระบุ"),
                "สถานะ": result.get("hours", "ไม่ระบุ"),
                "พิกัด_lat": result.get("gps_coordinates", {}).get("latitude", "ไม่ระบุ"),
                "พิกัด_lng": result.get("gps_coordinates", {}).get("longitude", "ไม่ระบุ")
            }
            
            # พยายามหา email จาก description หรือ snippet
            email = "ไม่ระบุ"
            if "snippet" in result:
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, result["snippet"])
                if emails:
                    email = emails[0]
            
            business_info["อีเมล"] = email
            
            return business_info
            
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return None
    
    def save_to_csv(self, businesses, filename=None):
        """
        บันทึกข้อมูลเป็นไฟล์ CSV
        
        Args:
            businesses (list): รายการข้อมูลธุรกิจ
            filename (str): ชื่อไฟล์ (ถ้าไม่ระบุจะใช้วันที่ปัจจุบัน)
        
        Returns:
            str: ชื่อไฟล์ที่บันทึก
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_search_results_{timestamp}.csv"
        
        df = pd.DataFrame(businesses)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        return filename

def main():
    # โหลดค่า configuration จาก .env
    app_title = os.getenv('APP_TITLE', 'ระบบค้นหาธุรกิจใน Google Maps')
    
    st.set_page_config(
        page_title=app_title,
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS สำหรับ Modern Dashboard
    st.markdown("""
    <style>
    /* Import Google Font Noto Sans Thai */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
    
    /* Apply font to all elements */
    * {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    
    /* Main dashboard styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        font-family: 'Noto Sans Thai', sans-serif;
    }
    
    .metric-card {
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
        color: white;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .metric-card.blue {
        background: linear-gradient(135deg, #4e73df 0%, #224abe 100%);
    }
    
    .metric-card.green {
        background: linear-gradient(135deg, #1cc88a 0%, #13855c 100%);
    }
    
    .metric-card.orange {
        background: linear-gradient(135deg, #f6c23e 0%, #dda20a 100%);
    }
    
    .metric-card.red {
        background: linear-gradient(135deg, #e74a3b 0%, #c0392b 100%);
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
        font-family: 'Noto Sans Thai', sans-serif;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-label {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin: 0;
        font-weight: 500;
        font-family: 'Noto Sans Thai', sans-serif;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    
    .search-form {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .results-table {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fix expander text overlap */
    .streamlit-expanderHeader {
        font-family: 'Noto Sans Thai', sans-serif !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
    }
    
    .streamlit-expanderContent {
        font-family: 'Noto Sans Thai', sans-serif !important;
        line-height: 1.6 !important;
    }
    
    /* Fix span element spacing */
    span {
        line-height: 1.5 !important;
    }
    
    /* Fix markdown in expander */
    .streamlit-expanderContent .stMarkdown {
        line-height: 1.6 !important;
    }
    
    /* Hide selectbox dropdown arrows */
     [data-testid="stSelectbox"] svg {
         display: none !important;
     }
     
     /* Hide Material Icons */
     span[data-testid="stIconMaterial"] {
         display: none !important;
     }
    </style>
    
    <script>
    // Remove keyboard_arrow_down text from DOM
    function removeKeyboardArrowText() {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        
        while (node = walker.nextNode()) {
            if (node.textContent.includes('keyboard_arrow_down')) {
                textNodes.push(node);
            }
        }
        
        textNodes.forEach(textNode => {
            textNode.textContent = textNode.textContent.replace(/keyboard_arrow_down/g, '');
        });
    }
    
    // Run on page load and periodically
    document.addEventListener('DOMContentLoaded', removeKeyboardArrowText);
    setInterval(removeKeyboardArrowText, 1000);
    </script>
    """, unsafe_allow_html=True)
    
    # Header Dashboard
    st.markdown(f"""
    <div class="main-header">
        <h1>🗺️ {app_title}</h1>
        <p>ค้นหาและรวบรวมข้อมูลธุรกิจจาก Google Maps อย่างมีประสิทธิภาพ</p>
    </div>
    """, unsafe_allow_html=True)
    
    # สร้าง BusinessSearcher instance
    searcher = BusinessSearcher(API_KEY)
    
    # Metric Cards Dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card blue">
            <p class="metric-number">77</p>
            <p class="metric-label">จังหวัดทั้งหมด</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card green">
            <p class="metric-number">50+</p>
            <p class="metric-label">ประเภทธุรกิจ</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card orange">
            <p class="metric-number" id="search-count">0</p>
            <p class="metric-label">ผลลัพธ์ล่าสุด</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card red">
            <p class="metric-number">API</p>
            <p class="metric-label">สถานะเชื่อมต่อ</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ข้อมูลจังหวัดและอำเภอ
    provinces_districts = {
        "กรุงเทพมหานคร": ["พระนคร", "ดุสิต", "หนองจอก", "บางรัก", "บางเขน", "บางกะปิ", "ปทุมวัน", "ป้อมปราบศัตรูพ่าย", "พระโขนง", "มีนบุรี", "ลาดกระบัง", "ยานนาวา", "สัมพันธวงศ์", "พญาไท", "ธนบุรี", "บางกอกใหญ่", "ห้วยขวาง", "คลองสาน", "ตลิ่งชัน", "บางกอกน้อย", "บางขุนเทียน", "ภาษีเจริญ", "หนองแขม", "ราษฎร์บูรณะ", "บางพลัด", "ดินแดง", "บึงกุ่ม", "สาทร", "บางซื่อ", "จตุจักร", "บางคอแหลม", "ประเวศ", "คลองเตย", "สวนหลวง", "จอมทอง", "ดอนเมือง", "ราชเทวี", "ลาดพร้าว", "วัฒนา", "บางแค", "หลักสี่", "สายไหม", "คันนายาว", "สะพานพุทธ", "วังทองหลาง", "คลองสามวา", "บางนา", "ทวีวัฒนา", "ทุ่งครุ", "บางบอน"],
        "กระบี่": ["เมืองกระบี่", "เขาพนม", "เกาะลันตา", "คลองท่อม", "อ่าวลึก", "ปลายพระยา", "ลำทับ", "เหนือคลอง"],
        "กาญจนบุรี": ["เมืองกาญจนบุรี", "ไทรโยค", "บ่อพลอย", "ศรีสวัสดิ์", "ท่าม่วง", "ท่ามะกา", "พนมทวน", "เลาขวัญ", "ด่านมะขามเตี้ย", "หนองปรือ", "ห้วยกระเจา", "ทองผาภูมิ", "สังขละบุรี"],
        "กาฬสินธุ์": ["เมืองกาฬสินธุ์", "นามน", "กมลาไสย", "ร่องคำ", "กุฉินารายณ์", "เขื่องใน", "ดอนจาน", "ห้วยเม็ก", "สมเด็จ", "ห้วยผึ้ง", "ฆ้องชัย", "ยางตลาด", "เฟื่องนคร", "ท่าคันโท", "หนองกุงศรี", "สหัสขันธ์", "คำม่วง", "ทุ่งศรีอุดม"],
        "กำแพงเพชร": ["เมืองกำแพงเพชร", "ไทรงาม", "คลองลาน", "ขาณุวรลักษบุรี", "บึงสามัคคี", "ทรายทองวัฒนา", "พรานกระต่าย", "ลานกระบือ", "ปางศิลาทอง", "เมืองทราย", "โกสัมพีนคร"],
        "ขอนแก่น": ["เมืองขอนแก่น", "บ้านไผ่", "พล", "เวียงเก่า", "เวียงเยี่ยม", "กระนวน", "หนองเรือ", "บ้านฝาง", "อุบลรัตน์", "น้ำพอง", "เปือยน้อย", "โคกโพธิ์ไชย", "หนองนาคำ", "บ้านแฮด", "โนนศิลา", "ชุมแพ", "สีชมพู", "หนองสองห้อง", "ภูเวียง", "มัญจาคีรี", "ผักปัง", "ภูผาม่าน", "สามสูง", "โครงการ", "หนองกุงศรี"],
        "จันทบุรี": ["เมืองจันทบุรี", "ขลุง", "ท่าใหม่", "โป่งน้ำร้อน", "มะขาม", "แก่งหางแมว", "นายายอาม", "สอยดาว", "แหลมสิงห์", "เขาคิชฌกูฏ"],
        "ฉะเชิงเทรา": ["เมืองฉะเชิงเทรา", "บางคล้า", "บางน้ำเปรี้ยว", "บางปะกง", "พนมสารคาม", "ราชสาส์น", "สนามชัยเขต", "แปลงยาว", "ท่าตะเกียบ", "คลองเขื่อน", "บ้านโพธิ์"],
        "ชลบุรี": ["เมืองชลบุรี", "บ้านบึง", "หนองใหญ่", "บางละมุง", "พานทอง", "พนัสนิคม", "ศรีราชา", "เกาะสีชัง", "สัตหีบ", "บ่อทอง", "เกาะจันทร์"],
        "ชัยนาท": ["เมืองชัยนาท", "มโนรมย์", "วัดสิงห์", "สรรพยา", "สรรคบุรี", "หันคา", "หนองมะโมง", "เนินขาม"],
        "ชัยภูมิ": ["เมืองชัยภูมิ", "เกษตรสมบูรณ์", "กงไกรลาศ", "จัตุรัส", "บำเหน็จณรงค์", "หนองบัวระเหว", "คอนสวรรค์", "คอนสาร", "ภูเขียว", "เทพสถิต", "ภักดีชุมพล", "หนองบัวแดง", "แก้งคร้อ", "บ้านเขว้า", "โนนแดง", "จัตุรัส", "ซับใหญ่"],
        "ชุมพร": ["เมืองชุมพร", "ท่าแซะ", "ปะทิว", "หลังสวน", "ละแม", "ทุ่งตะโก", "สวี", "ทุ่งใหญ่"],
        "เชียงราย": ["เมืองเชียงราย", "เวียงชัย", "เชียงของ", "เทิง", "พาน", "ป่าแดด", "แม่จัน", "เชียงแสน", "แม่สาย", "แม่สรวย", "วียงป่าเป้า", "พญาเม็งราย", "เวียงแก่น", "ขุนตาล", "แม่ฟ้าหลวง", "แม่ลาว", "เวียงเชียงรุ้ง", "ดอยหลวง"],
        "เชียงใหม่": ["เมืองเชียงใหม่", "ดอยสะเก็ด", "แม่ริม", "สะเมิง", "แม่แตง", "แม่อ่อน", "ฝาง", "ไชยปราการ", "เมืองแปด", "สันทราย", "สันกำแพง", "สันป่าตอง", "หางดง", "ฮอด", "ดอยเต่า", "อมก๋อย", "เสาไห้", "แม่วาง", "พร้าว", "แม่ออน", "ดอยหลวง", "เวียงแหง", "ไชยปราการ", "แม่แจ่ม"],
        "ตรัง": ["เมืองตรัง", "กันตัง", "ย่านตาขาว", "ปะเลียน", "รัษฎา", "หาดสำราญ", "วังวิเศษ", "นาโยง", "ห้วยยอด", "สิเกา"],
        "ตราด": ["เมืองตราด", "คลองใหญ่", "เขาสมิง", "บ่อไร่", "แหลมงอบ", "เกาะกูด", "เกาะช้าง"],
        "ตาก": ["เมืองตาก", "บ้านตาก", "สามเงา", "แม่ระมาด", "ท่าสองยาง", "แม่สอด", "พบพระ", "อุ้มผาง", "วังเจ้า"],
        "นครนายก": ["เมืองนครนายก", "ปากพลี", "บ้านนา", "องครักษ์"],
        "นครปฐม": ["เมืองนครปฐม", "กำแพงแสน", "นครชัยศรี", "ดอนตูม", "บางเลน", "สามพราน", "พุทธมณฑล"],
        "นครพนม": ["เมืองนครพนม", "ปลาปาก", "ท่าอุเทน", "บ้านแพง", "ศรีสงคราม", "นาแก", "โพนสวรรค์", "นาทม", "เรณูนคร", "นาหว้า", "ธาตุพนม", "วังยาง"],
        "นครราชสีมา": ["เมืองนครราชสีมา", "ครบุรี", "เสิงสาง", "โคกกรวด", "ชุมพวง", "โนนแดง", "โนนสูง", "ขามสะแกแสง", "บัวใหญ่", "ประทาย", "ปักธงชัย", "พิมาย", "ห้วยแถลง", "ชัยภูมิ", "คง", "บ้านเลื่อม", "จักราช", "ครบุรี", "เฉลิมพระเกียรติ", "สูงเนิน", "สีดา", "เทพารักษ์", "เมืองยาง", "ลำทะเมนชัย", "วังน้ำเขียว", "พระทองคำ", "บัวลาย", "แก้งสนามนาง", "โนนไทย", "โชคชัย", "ด่านขุนทด"],
        "นครศรีธรรมราช": ["เมืองนครศรีธรรมราช", "พรหมคีรี", "ลานสกา", "ฉวาง", "พิปูน", "เชียรใหญ่", "ท่าศาลา", "ทุ่งสง", "ปากพนัง", "ร่อนพิบูลย์", "สิชล", "ขนอม", "หัวไทร", "บางขัน", "ทุ่งใหญ่", "นบพิตำ", "นาบอน", "ช้างกลาง", "ท่าตะเกียบ", "เฉลิมพระเกียรติ", "จุฬาภรณ์", "พระพรหม", "นพพิตำ"],
        "นครสวรรค์": ["เมืองนครสวรรค์", "โกรกพระ", "ชุมแสง", "โกรกพระ", "ไผ่สีทอง", "บรรพตพิสัย", "เก้าเลี้ยว", "ตาคลี", "ลาดยาว", "ตากฟ้า", "แม่วงก์", "แม่พิงค์", "ชุมตาบง", "หนองบัว", "ท่าตะโก"],
        "นนทบุรี": ["เมืองนนทบุรี", "บางกรวย", "บางใหญ่", "บางบัวทอง", "ไทรน้อย", "ปากเกร็ด"],
        "นราธิวาส": ["เมืองนราธิวาส", "ตากใบ", "บาเจาะ", "ยี่งอ", "ระแงะ", "รือเสาะ", "ศรีสาคร", "แว้ง", "สุคิริน", "สุไหงโก-ลก", "สุไหงปาดี", "จะแนะ", "เจาะไอร้อง"],
        "น่าน": ["เมืองน่าน", "แม่จริม", "บ้านหลวง", "นาน้อย", "ปัว", "ท่าวังผา", "เวียงสา", "ทุ่งช้าง", "เฉลิมพระเกียรติ", "นาหมื่น", "สันติสุข", "บ้านหลวง", "เชียงกลาง", "ภูเพียง", "ทุ่งช้าง"],
        "บึงกาฬ": ["เมืองบึงกาฬ", "โซ่พิสัย", "เซกา", "บุ่งคล้า", "ศรีวิไล", "บึงโขงหลง", "ปากคาด", "โพนเจริญ"],
        "บุรีรัมย์": ["เมืองบุรีรัมย์", "กระสัง", "นางรอง", "หนองกี่", "หนองหงส์", "แคนดง", "ประโคนชัย", "ลำปลายมาศ", "สตึก", "ปะคำ", "นาโพธิ์", "เฉลิมพระเกียรติ", "โนนสุวรรณ", "ชำนิ", "บ้านกรวด", "หูทะเล", "โนนดินแดง", "เมืองยาง", "แคนดง", "พลับพลาชัย", "หนองแสง", "บ้านใหม่ไชยพจน์", "คูเมือง"],
        "ปทุมธานี": ["เมืองปทุมธานี", "คลองหลวง", "ธัญบุรี", "รังสิต", "หนองเสือ", "ลาดหลุมแก้ว", "สามโคก"],
        "ประจวบคีรีขันธ์": ["เมืองประจวบคีรีขันธ์", "กุยบุรี", "ทับสะแก", "บางสะพาน", "บางสะพานน้อย", "ปราณบุรี", "หัวหิน", "สามร้อยยอด"],
        "ปราจีนบุรี": ["เมืองปราจีนบุรี", "กบินทร์บุรี", "นาดี", "บ้านสร้าง", "ประจันตคาม", "ศรีมหาโพธิ", "ศรีมโหสถ", "เกาะรูปช้าง"],
        "ปัตตานี": ["เมืองปัตตานี", "โคกโพธิ์", "หนองจิก", "ปะนาเระ", "มายอ", "ทุ่งยางแดง", "สายบุรี", "ไม้แก่น", "โนนจิก", "ยะรัง", "ยะหริ่ง", "กะพ้อ"],
        "พระนครศรีอยุธยา": ["พระนครศรีอยุธยา", "ท่าเรือ", "นครหลวง", "บางไทร", "บางปะอิน", "บางปะหัน", "ผักไห่", "ลาดบัวหลวง", "วังน้อย", "เสนา", "บางซ้าย", "อุทัย", "มหาราช", "บ้านแพรก", "ภาชี", "ลาติวงศ์"],
        "พังงา": ["เมืองพังงา", "เกาะยาว", "กะปง", "ตะกั่วทุ่ง", "ตะกั่วป่า", "คุระบุรี", "ทับปุด", "ท้ายเหมือง"],
        "พัทลุง": ["เมืองพัทลุง", "กงหรา", "เขาชัยสน", "ตำบลใหญ่", "ป่าบอน", "ป่าพะยอม", "ศรีนครินทร์", "ศรีบรรพต", "ตรัง", "บางแก้ว", "ปากพะยูน"],
        "พิจิตร": ["เมืองพิจิตร", "วังทรายพูน", "โพธิ์ประทับช้าง", "ตะพานหิน", "บางมูลนาก", "โพทะเล", "สามง่าม", "ทับคล้อ", "สากเหล็ก", "บึงนาราง", "ดงเจริญ", "วชิรบารมี"],
        "พิษณุโลก": ["เมืองพิษณุโลก", "นครไทย", "ชาติตระการ", "บางระกำ", "บางกระทุ่ม", "นิคมพัฒนา", "วัดโบสถ์", "พรหมพิราม", "เนินมะปราง"],
        "เพชรบุรี": ["เมืองเพชรบุรี", "เขาย้อย", "หนองหญ้าปล้อง", "ชะอำ", "ท่ายาง", "บ้านลาด", "บ้านแหลม", "แก่งกระจาน"],
        "เพชรบูรณ์": ["เมืองเพชรบูรณ์", "ชนแดน", "หล่มสัก", "หล่มเก่า", "วิเชียรบุรี", "ศรีเทพ", "เขาค้อ", "น้ำหนาว", "บึงสามพัน", "วังโป่ง", "หนองไผ่"],
        "แพร่": ["เมืองแพร่", "ร้องกวาง", "ลอง", "สอง", "เด่นชัย", "สูงเม่น", "วังชิ้น", "หนองม่วงไข่"],
        "ภูเก็ต": ["เมืองภูเก็ต", "กะทู้", "ถลาง"],
        "มหาสารคาม": ["เมืองมหาสารคาม", "กันทรวิชัย", "เชิงดอย", "บรบือ", "เกษตรวิสัย", "กุดรัง", "โกสุมพิสัย", "กันทรลักษ์", "ศรีรัตนะ", "พยัคฆภูมิพิสัย", "วาปีปทุม", "นาดูน", "ยางสีสุราช"],
        "มุกดาหาร": ["เมืองมุกดาหาร", "นิคมคำสร้อย", "ดอนตาล", "ดงหลวง", "คำชะอี", "หว้านใหญ่", "เดิมบางนางบวช"],
        "แม่ฮ่องสอน": ["เมืองแม่ฮ่องสอน", "ขุนยวม", "ปาย", "แม่สะเรียง", "แม่ลาน้อย", "สบเมย", "ปางมะผ้า"],
        "ยโสธร": ["เมืองยโสธร", "กุดชุม", "ไทยเจริญ", "กันทรารมย์", "ป่าติ้ว", "มหาชนะชัย", "ค้อวัง", "เลิงนกทา", "ไผ่ใส"],
        "ยะลา": ["เมืองยะลา", "เบตง", "บันนังสตา", "ธารโต", "ยะหา", "กาบัง", "กรงปินัง", "รามัน"],
        "ร้อยเอ็ด": ["เมืองร้อยเอ็ด", "เกษตรวิสัย", "ปทุมรัตต์", "จตุรพักตรพิมาน", "ทุ่งเขาหลวง", "ปธานนิคม", "โพนทอง", "โพธิ์ชัย", "เมืองสรวง", "จังหาร", "เชียงขวัญ", "เสลภูมิ", "สุวรรณภูมิ", "โพนทราย", "หนองพอก", "เอื้อมใส", "โพธิ์ชัย", "อาจสามารถ", "ศรีสมเด็จ"],
        "ระนอง": ["เมืองระนอง", "ละอุ่น", "กะปง", "สุขสำราญ"],
        "ระยอง": ["เมืองระยอง", "บ้านฉาง", "แกลง", "วังจันทร์", "บ้านค่าย", "ปลวกแดง", "เขาชะเมา", "นิคมพัฒนา"],
        "ราชบุรี": ["เมืองราชบุรี", "จอมบึง", "สวนผึ้ง", "ดำเนินสะดวก", "บ้านโป่ง", "บางแพ", "โพธาราม", "ปากท่อ", "วัดเพลง", "บ้านคา"],
        "ลพบุรี": ["เมืองลพบุรี", "พัฒนานิคม", "โคกเจริญ", "ชัยบาดาล", "ท่าวุ้ง", "บ้านหมี่", "ท่าหลวง", "ลำสนธิ", "โคกสำโรง", "ซับสมบูรณ์", "หนองม่วง"],
        "ลำปาง": ["เมืองลำปาง", "แม่เมาะ", "เกาะคา", "แม่ทะ", "แม่พริก", "วังเหนือ", "เถิน", "แจ้ห่ม", "งาว", "เสริมงาม", "แม่ทา", "สบปราบ", "ห้างฉัตร"],
        "ลำพูน": ["เมืองลำพูน", "ป่าซาง", "ลี้", "ทุ่งหัวช้าง", "บ้านโฮ่ง", "บ้านธิ", "เวียงหนองล่อง", "ทุ่งหัวช้าง"],
        "เลย": ["เมืองเลย", "ท่าลี่", "นาด้วง", "ภูเรือ", "ภูกระดึง", "ภูหลวง", "วังสะพุง", "เอราวัณ", "ปากชม", "ชุมแพ", "นาแห้ว", "ด่านซ้าย"],
        "ศรีสะเกษ": ["เมืองศรีสะเกษ", "ยางชุมน้อย", "กันทรารมย์", "กันทรลักษ์", "ราษีไศล", "อุทุมพรพิสัย", "บึงบูรพ์", "ห้วยทับทัน", "โนนคูณ", "ศิลาลาด", "มูลนาคร", "ภูสิงห์", "เมืองจันทร์", "เบญจลักษ์", "พรรณนานิคม", "โพธิ์ศรีสุวรรณ", "ศรีรัตนะ", "วังหิน", "ปรางค์กู่", "ขุขันธ์", "ไพรบึง", "โพนทอง"],
        "สกลนคร": ["เมืองสกลนคร", "กุสุมาลย์", "กุดบาก", "พรรณานิคม", "พังโคน", "อากาศอำนวย", "สว่างแดนดิน", "วาริชภูมิ", "นิคมน้ำอูน", "วานรนิวาส", "ท่าแร่", "เจริญศิลป์", "โคกศรีสุพรรณ", "ภูพาน", "ส่องดาว", "ตาลสุม", "โพนนาแก้ว", "อำนาจเจริญ"],
        "สงขลา": ["เมืองสงขลา", "สทิงพระ", "จะนะ", "นาทวี", "เทพา", "สะบ้าย้อย", "ระโนด", "กระแสสินธุ์", "รัตภูมิ", "สะเดา", "หาดใหญ่", "นาหม่อม", "ควนเนียง", "บางกล่ำ", "สิงหนคร", "คลองหอยโข่ง"],
        "สตูล": ["เมืองสตูล", "ละงู", "ทุ่งหว้า", "มะนัง", "ท่าแพ", "ควนโดน", "ควนกาหลง"],
        "สมุทรปราการ": ["เมืองสมุทรปราการ", "บางบ่อ", "บางพลี", "พระประแดง", "พระสมุทรเจดีย์", "บางเสาธง"],
        "สมุทรสงคราม": ["เมืองสมุทรสงคราม", "บางคนที", "อัมพวา"],
        "สมุทรสาคร": ["เมืองสมุทรสาคร", "กระทุ่มแบน", "บ้านแพ้ว"],
        "สระแก้ว": ["เมืองสระแก้ว", "คลองหาด", "ตาพระยา", "วังน้ำเย็น", "อรัญประเทศ", "วัฒนานคร", "โคกสูง", "วังสมบูรณ์", "เขาฉกรรจ์"],
        "สระบุรี": ["เมืองสระบุรี", "แก่งคอย", "หนองแค", "วิหารแดง", "หนองแซง", "บ้านหมอ", "ดอนพุด", "หนองโดน", "พระพุทธบาท", "เสาไห้", "มวกเหล็ก", "วังม่วง", "เฉลิมพระเกียรติ"],
        "สิงห์บุรี": ["เมืองสิงห์บุรี", "บางระจัน", "ค่ายบางระจัน", "อินทร์บุรี", "ท่าช้าง", "พรหมบุรี"],
        "สุโขทัย": ["เมืองสุโขทัย", "บ้านด่านลานหอย", "คีรีมาศ", "กงไกรลาศ", "ศรีสำโรง", "ศรีนคร", "ทุ่งเสลี่ยม", "ศรีสัชนาลัย", "สวรรคโลก"],
        "สุพรรณบุรี": ["เมืองสุพรรณบุรี", "เดิมบางนางบวช", "ด่านช้าง", "บางปลาม้า", "ศรีประจันต์", "ดอนเจดีย์", "สองพี่น้อง", "สามชุก", "อู่ทอง", "หนองหญ้าไซ"],
        "สุราษฎร์ธานี": ["เมืองสุราษฎร์ธานี", "กาญจนดิษฐ์", "ดอนสัก", "เกาะสมุย", "เกาะพะงัน", "ไชยา", "ท่าชนะ", "คีรีรัฐนิคม", "บ้านตาขุน", "พนม", "ท่าช้าง", "บ้านนาสาร", "บ้านนาเดิม", "เคียนซา", "เวียงสระ", "พระแสง", "วิภาวดี", "ชัยบุรี", "ไพบูลย์"],
        "สุรินทร์": ["เมืองสุรินทร์", "ชุมพลบุรี", "ท่าตูม", "จอมพระ", "ปราสาท", "กาบเชิง", "รัตนบุรี", "สนม", "ศีขรภูมิ", "สังขะ", "ลำดวน", "สำโรงทาบ", "บัวเชด", "พนมดงรัก", "ศรีณรงค์", "เมืองจันทร์", "โนนนารายณ์"],
        "หนองคาย": ["เมืองหนองคาย", "ท่าบ่อ", "โพนพิสัย", "โซ่พิสัย", "เฝ้าไร่", "รัตนวาปี", "สังคม", "ศรีเชียงใหม่"],
        "หนองบัวลำภู": ["เมืองหนองบัวลำภู", "นาคลาง", "เสียว", "นาวัง", "โนนสัง", "สุวรรณคูหา"],
        "อ่างทอง": ["เมืองอ่างทอง", "ไชโย", "ป่าโมก", "โพธิ์ทอง", "แสวงหา", "วิเศษชัยชาญ", "สามโก้"],
        "อำนาจเจริญ": ["เมืองอำนาจเจริญ", "ชานุมาน", "ปทุมราชวงศา", "พนา", "หัวตะพาน", "เสนางคนิคม", "ลืออำนาจ"],
        "อุดรธานี": ["เมืองอุดรธานี", "กุมภวาปี", "โนนสะอาด", "นาโยง", "หนองวัวซอ", "กุดจับ", "บ้านผือ", "เพ็ญ", "สร้างคอม", "วังสามหมอ", "ไชยวาน", "ศรีธาตุ", "น้ำโสม", "หนองแสง", "บ้านดุง", "ทุ่งฝน", "ประจักษ์ศิลปาคม", "กุมภวาปี", "โนนสะอาด", "หนองหาน"],
        "อุตรดิตถ์": ["เมืองอุตรดิตถ์", "ตรอน", "ลับแล", "ท่าปลา", "น้ำปาด", "ฟากท่า", "บ้านโคก", "ทองแสนขัน", "น้ำปาด"],
        "อุทัยธานี": ["เมืองอุทัยธานี", "ทัพทัน", "สว่างอารมณ์", "หนองขาหย่าง", "หนองฉาง", "บ้านไร่", "ลานสัก", "ห้วยคต"],
        "อุบลราชธานี": ["เมืองอุบลราชธานี", "ศรีเมืองใหม่", "โขงเจียม", "เดชอุดม", "น้ำยืน", "บุณฑริก", "ตระการพืชผล", "กุดข้าวปุ้น", "ม่วงสามสิบ", "วารินชำราบ", "พิบูลมังสาหาร", "ตาลสุม", "โพธิ์ไทร", "สำโรง", "ดอนมดแดง", "สิรินธร", "ทุ่งศรีอุดม", "นาจะหลวย", "เขื่องใน", "เขมราฐ", "โดมใหญ่", "อำนาจเจริญ", "ลือใส", "สว่างวีระวงศ์", "น้ำขุ่น"]
    }
    
    provinces = list(provinces_districts.keys())
    
    # รายการประเภทธุรกิจ
    business_types = [
        "ร้านอาหาร", "โรงแรม", "ร้านกาแฟ", "คลินิก", "โรงพยาบาล", "ร้านเสื้อผ้า", "ร้านขายยา", "ธนาคาร",
        "ปั๊มน้ำมัน", "ร้านสะดวกซื้อ", "ซุปเปอร์มาร์เก็ต", "ร้านทำผม", "สปา", "ฟิตเนส", "โรงเรียน", "มหาวิทยาลัย",
        "ร้านหนังสือ", "ร้านดนตรี", "ร้านขายรถ", "อู่ซ่อมรถ", "ร้านซ่อมมือถือ", "ร้านคอมพิวเตอร์", "ร้านเบเกอรี่",
        "ร้านไอศกรีม", "ร้านดอกไม้", "ร้านของขวัญ", "ร้านเครื่องประดับ", "ร้านแว่นตา", "ร้านรองเท้า", "ร้านกระเป๋า",
        "ร้านเฟอร์นิเจอร์", "ร้านวัสดุก่อสร้าง", "ร้านจักรยาน", "ร้านกีฬา", "ร้านของเล่น", "ร้านสัตว์เลี้ยง",
        "คลีนิกสัตว์", "ร้านซักรีด", "ร้านถ่ายเอกสาร", "ไปรษณีย์", "สำนักงานขนส่ง", "ตลาด", "ห้างสรรพสินค้า",
        "โรงภาพยนตร์", "สวนสนุก", "พิพิธภัณฑ์", "วัด", "โบสถ์", "มัสยิด", "สถานีตำรวจ", "ที่ว่าการ"
    ]
    
    # Sidebar สำหรับการตั้งค่า
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0;">⚙️ การตั้งค่าการค้นหา</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # โหลดค่า default จาก .env
        default_business_type = os.getenv('DEFAULT_BUSINESS_TYPE', 'ทั้งหมด')
        default_province = os.getenv('DEFAULT_PROVINCE', 'ทั้งหมด')
        default_district = os.getenv('DEFAULT_DISTRICT', 'ทั้งหมด')
        
        # ฟอร์มการค้นหา
        with st.form("search_form"):
            # แถวแรก: ประเภทธุรกิจ
            st.markdown("**🏢 ประเภทธุรกิจ**")
            query = st.selectbox(
                "เลือกประเภทธุรกิจที่ต้องการค้นหา",
                options=business_types,
                index=0,
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # แถวที่สอง: จังหวัด
            st.markdown("**🗺️ จังหวัด**")
            selected_province = st.selectbox(
                "เลือกจังหวัดที่ต้องการค้นหา",
                options=provinces,
                index=0,
                label_visibility="collapsed"
            )
            
            # แถวที่สาม: อำเภอ (อยู่ใต้จังหวัด)
            st.markdown("**📍 อำเภอ**")
            districts = provinces_districts.get(selected_province, [])
            selected_district = st.selectbox(
                "เลือกอำเภอที่ต้องการค้นหา",
                options=["ทุกอำเภอ"] + districts,
                index=0,
                label_visibility="collapsed"
            )
            
            # สร้าง location string สำหรับการค้นหา
            if selected_district == "ทุกอำเภอ":
                location = selected_province
            else:
                location = f"{selected_district}, {selected_province}"
            
            st.markdown("---")
            
            # แถวที่สี่: จำนวนผลลัพธ์
            st.markdown("**📊 จำนวนผลลัพธ์**")
            num_results = st.slider(
                "เลือกจำนวนผลลัพธ์ที่ต้องการ",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                label_visibility="collapsed"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ปุ่มค้นหา
            search_button = st.form_submit_button(
                "🔍 เริ่มค้นหาธุรกิจ",
                use_container_width=True
            )
    
    # หน้าหลัก
    if search_button and query:
        with st.spinner(f"กำลังค้นหา '{query}' ใน {location}..."):
            businesses = searcher.search_businesses(query, location, num_results)
        
        if businesses:
            # อัพเดท metric card สำหรับจำนวนผลลัพธ์
            st.markdown(f"""
            <script>
                document.getElementById('search-count').innerText = '{len(businesses)}';
            </script>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="success-message" style="background: linear-gradient(90deg, #28a745 0%, #20c997 100%); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; text-align: center;">
                ✅ พบธุรกิจ <strong>{len(businesses)}</strong> แห่ง ในพื้นที่ <strong>{location}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # แสดงผลลัพธ์
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("📋 ผลลัพธ์การค้นหา")
                
                # แสดงข้อมูลในรูปแบบตาราง modern
                df = pd.DataFrame(businesses)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ชื่อธุรกิจ": st.column_config.TextColumn(
                            "🏢 ชื่อธุรกิจ",
                            width="large"
                        ),
                        "ที่อยู่": st.column_config.TextColumn(
                            "📍 ที่อยู่",
                            width="large"
                        ),
                        "เบอร์โทรศัพท์": st.column_config.TextColumn(
                            "📞 เบอร์โทร",
                            width="medium"
                        ),
                        "คะแนนรีวิว": st.column_config.NumberColumn(
                            "⭐ เรตติ้ง",
                            width="small",
                            format="%.1f"
                        ),
                        "จำนวนรีวิว": st.column_config.NumberColumn(
                            "💬 รีวิว",
                            width="small"
                        )
                    }
                )
            
            with col2:
                st.subheader("💾 ดาวน์โหลดข้อมูล")
                
                # ปุ่มดาวน์โหลด CSV
                csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 ดาวน์โหลด CSV",
                    data=csv_data,
                    file_name=f"business_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # ปุ่มดาวน์โหลด Excel
                from io import BytesIO
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📊 ดาวน์โหลด Excel",
                    data=excel_data,
                    file_name=f"business_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # แสดงรายละเอียดแต่ละธุรกิจ
            st.subheader("🏢 รายละเอียดธุรกิจ")
            
            for i, business in enumerate(businesses, 1):
                with st.expander(f"{i}. {business['ชื่อธุรกิจ']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ที่อยู่:** {business['ที่อยู่']}")
                        st.write(f"**เบอร์โทรศัพท์:** {business['เบอร์โทรศัพท์']}")
                        st.write(f"**อีเมล:** {business['อีเมล']}")
                        st.write(f"**เว็บไซต์:** {business['เว็บไซต์']}")
                    
                    with col2:
                        st.write(f"**ประเภทธุรกิจ:** {business['ประเภทธุรกิจ']}")
                        st.write(f"**คะแนนรีวิว:** {business['คะแนนรีวิว']}")
                        st.write(f"**จำนวนรีวิว:** {business['จำนวนรีวิว']}")
                        st.write(f"**สถานะ:** {business['สถานะ']}")
        
        else:
            st.warning("ไม่พบผลลัพธ์การค้นหา กรุณาลองใช้คำค้นหาอื่น")
    
    elif search_button and not query:
        st.error("กรุณาระบุประเภทธุรกิจที่ต้องการค้นหา")
    


if __name__ == "__main__":
    main()