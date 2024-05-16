# ========================================== import library ============================================
import streamlit as st
from streamlit_option_menu import option_menu
from impala.dbapi import connect
import math
import time
# ======================================= Cấu hình streamlit ===========================================
# Cấu hình trang Streamlit
st.set_page_config(page_title='Demo App Impala Project - Vector Search', page_icon=':cyclone:', layout='wide')
# css
def css_get():
    return """
    .stApp {
    background: url("https://images2.alphacoders.com/133/1331312.png") no-repeat center center fixed !important;
    background-size: cover !important;
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.604); 
        
    }

    .nav, .nav-item {
        font-family: Arial, sans-serif;
    }


    .st-ar {
        font-family: 'Arial', sans-serif;
    }

    .st-emotion-cache-18ni7ap {
        background: linear-gradient(to right,#a9bce1, #fdfcfd);
    }

    .st-emotion-cache-6qob1r  {
        background: #a9bce1;
    }

    .title {
        text-align: center;
        font-size: 60px;
    }

    .page {
        text-align: center;
        font-size: 20px;
    }

    .subheader {
        text-align: left;
        font-size: 30px;
    }

    .subheader-text {
        font-size: 20px;
    }

    .st-emotion-cache-q3uqly {
        background: rgb(169, 169, 255);
        border: 2px solid rgb(0, 0, 0)
    }

    .st-emotion-cache-q3uqly:hover {
        background: rgb(129, 129, 238);
        border: 2px solid rgb(149, 149, 238);
    }

    .st-emotion-cache-q3uqly:active {
        color: #b0c7ff;
    }

    .st-emotion-cache-1kyxreq, .st-emotion-cache-1r6slb0, .stButton , .stTextLabelWrapper  {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .stTextLabelWrapper  {
        margin-top: 30px;
    }

    .anime-name {
        text-align: left;
        text-decoration: none;
        font-size: 18px;
        color: black;
    }
    """
st.markdown(f'<style>{css_get()}</style>', unsafe_allow_html=True)

# Sidebar 
with st.sidebar:
    selected = option_menu("Vector Search Anime",["Anime Recommend System"],
                           icons=['search'], menu_icon="cast", default_index=0,
                           styles={
                                "container": {"font-family": "Monospace"},
                                "icon": {"color":"#71738d"}, 
                                "nav-link": {"--hover-color": "#d2cdfa","font-family": "Monospace"},
                                "nav-link-selected": {"font-family": "Monospace","background-color": "#a9a9ff"},
                            }
                           )

# ======================================= Impala Query =========================================
IP = "192.168.1.65"
def Impala_Query(query,db_name=""):
    try:
        conn = connect(host=IP)
        cursor = conn.cursor()

        # Thực hiện truy vấn SQL để liệt kê các cơ sở dữ liệu
        if (db_name!= ""):
            cursor.execute(f"USE {db_name}")
        cursor.execute(query)
        
        # Lấy kết quả truy vấn
        result = cursor.fetchall()

        # Đóng kết nối
        cursor.close()
        conn.close()
        return result
    except:
        return None
    
class Vector:
    def __init__(self,vector_id, vector_inf):
        self.vector_id = vector_id
        self.vector_inf = vector_inf
        
    def length(self):
        length = 0
        for inf in self.vector_inf:
            length += inf[1] ** 2
        return math.sqrt(length)

def similar_cosine(vector_a,vector_b):
    dot_vector = 0
    for inf_a in vector_a.vector_inf:
        for inf_b in vector_b.vector_inf:
            if inf_a[0] == inf_b[0]:
                dot_vector += inf_a[1] * inf_b[1]
    return dot_vector / (vector_a.length() * vector_b.length())
    
def Vector_query(title):
    anime_mapping = Impala_Query(f"SELECT vector_id FROM anime_mapping WHERE title='{title}'","vectordb")
    if anime_mapping == None:
        print("Không có kết quả nào!")
        return None
    else:
        anime_vector = Impala_Query(f"SELECT vector_index, vector_value FROM anime_vector WHERE vector_id={anime_mapping[0][0]}","vectordb")
        return Vector(anime_mapping[0][0],anime_vector)
    
def Vector_search(vector,limit=10):
    full_anime_vector = Impala_Query(f"SELECT * FROM anime_vector","vectordb")
    vectors = []
    anime_vector_dict = {}
    for anime_vector in full_anime_vector:
        key = anime_vector[0]
        if key in anime_vector_dict:
            anime_vector_dict[key].append(anime_vector[1:3])
        else:
            anime_vector_dict[key] = [anime_vector[1:3]]
    for key in anime_vector_dict:
        vectors.append(Vector(key,anime_vector_dict[key]))
        
    sim_cosine_dict = {}
    for vector_temp in vectors:
        sim_cosine_dict[vector_temp.vector_id] = similar_cosine(vector,vector_temp)
    
    sorted_sim_cosine_dict = sorted(sim_cosine_dict.items(), key=lambda x: x[1], reverse=True)[1:limit+1]
    top_id = [inf[0] for inf in sorted_sim_cosine_dict]
    
    # Return result
    animes = Impala_Query(f"SELECT * FROM anime_mapping WHERE vector_id IN ({','.join(map(str,top_id))})","vectordb")
    return animes
    
    
# ===================================== Anime Recommend System =================================


def Anime_Search():
    # Title
    st.markdown('<h1 class="title">Anime Recommend System</h1>', unsafe_allow_html=True)
    st.markdown('<h1 class="subheader-text">Với hơn 16368 animes có trong kho, chúng tôi sẽ gợi ý cho bạn các bộ phim hay tương tự dựa trên bộ phim mà bạn đã coi gần đây. Hãy chọn bộ phim mà bạn đã coi gần đây</h1>', unsafe_allow_html=True)
    
    # Truy vấn Impala lấy lên danh sách title anime
    title_query = Impala_Query("SELECT title FROM anime_mapping","vectordb")
    titles = [title[0] for title in title_query]
    
    # Chọn một bộ phim đã xem gần đây
    title_option = st.selectbox("Một bộ phim mà bạn đã xem gần đây:", titles)
    
    # Chọn số bộ phim muốn gợi ý
    number_limit = st.number_input("Chọn số bộ phim muốn gợi ý", min_value=1, max_value=16367, value=10, step=1)
    
    # Thực hiện Vector Search
    start = time.time()
    vector = Vector_query(title_option)
    recommended_animes = Vector_search(vector,number_limit)
    end = time.time()
    st.write(f"Thời gian Vector Search: {end - start} giây")
    st.markdown('<h1 class="subheader-text">Kết quả gợi ý:</h1>', unsafe_allow_html=True)
    stt = 0
    for i in range(0,int(len(recommended_animes)/4)+1):
        anime_show =  st.columns(4)
        for col in anime_show:
            if stt < len(recommended_animes):
                with col:
                    st.markdown('<a href="'+ recommended_animes[stt][3] +'" style="text-decoration: none; color: black;"><img src="'+recommended_animes[stt][2] + '" width=150 height=250><h1 class="anime-name">'+recommended_animes[stt][1] +'</h1></a>',unsafe_allow_html=True)
                stt += 1
            
    
    
    
    
if selected=="Anime Recommend System":
    Anime_Search()
    