// import React, { useState } from "react";
// import { useTags } from './index.js'
// import api from '../api'

// export default function useRecipes () {
//   const [ recipes, setRecipes ] = useState([])
//   const [ recipesCount, setRecipesCount ] = useState(0)
//   const [ recipesPage, setRecipesPage ] = useState(1)
//   const { value: tagsValue, handleChange: handleTagsChange, setValue: setTagsValue } = useTags()

//   const handleLike = ({ id, toLike = true }) => {
//     const method = toLike ? api.addToFavorites.bind(api) : api.removeFromFavorites.bind(api)
//     method({ id }).then(res => {
//       const recipesUpdated = recipes.map(recipe => {
//         if (recipe.id === id) {
//           recipe.is_favorited = toLike
//         }
//         return recipe
//       })
//       setRecipes(recipesUpdated)
//     })
//     .catch(err => {
//       const { errors } = err
//       if (errors) {
//         alert(errors)
//       }
//     })
//   }

//   const handleAddToCart = ({ id, toAdd = true, callback }) => {
//     const method = toAdd ? api.addToOrders.bind(api) : api.removeFromOrders.bind(api)
//     method({ id }).then(res => {
//       const recipesUpdated = recipes.map(recipe => {
//         if (recipe.id === id) {
//           recipe.is_in_shopping_cart = toAdd
//         }
//         return recipe
//       })
//       setRecipes(recipesUpdated)
//       callback && callback(toAdd)
//     })
//     .catch(err => {
//       const { errors } = err
//       if (errors) {
//         alert(errors)
//       }
//     })
//   }

//   return {
//     recipes,
//     setRecipes,
//     recipesCount,
//     setRecipesCount,
//     recipesPage,
//     setRecipesPage,
//     tagsValue,
//     handleLike,
//     handleAddToCart,
//     handleTagsChange,
//     setTagsValue
//   }
// }
import React, { useState, useEffect } from "react";
import { useTags } from './index.js'
import { useLocation, useNavigate } from "react-router-dom";
import api from '../api'

export default function useRecipes () {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [ recipes, setRecipes ] = useState([])
  const [ recipesCount, setRecipesCount ] = useState(0)
  const [ recipesPage, setRecipesPage ] = useState(1)
  const { value: tagsValue, handleChange: handleTagsChange, setValue: setTagsValue } = useTags()

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const urlTags = params.getAll('tags');
    const page = parseInt(params.get('page')) || 1;
    
    setRecipesPage(page);
    
    api.getRecipes({ page, tags: urlTags })
      .then(res => {
        setRecipes(res.results);
        setRecipesCount(res.count);
      });
  }, [location.search]);

  const handleTagsChangeWithUrl = (newTagsValue) => {
    handleTagsChange(newTagsValue);
    
    const selectedTags = newTagsValue
      .filter(tag => tag.value)
      .map(tag => tag.slug);
    
    const params = new URLSearchParams(location.search);
    params.delete('tags');
    selectedTags.forEach(tag => {
      params.append('tags', tag);
    });
    params.set('page', '1');
    
    navigate(`/?${params.toString()}`);
  };

  const handleLike = ({ id, toLike = true }) => {
    const method = toLike ? api.addToFavorites.bind(api) : api.removeFromFavorites.bind(api)
    method({ id }).then(res => {
      const recipesUpdated = recipes.map(recipe => {
        if (recipe.id === id) {
          recipe.is_favorited = toLike
        }
        return recipe
      })
      setRecipes(recipesUpdated)
    })
    .catch(err => {
      const { errors } = err
      if (errors) {
        alert(errors)
      }
    })
  }

  const handleAddToCart = ({ id, toAdd = true, callback }) => {
    const method = toAdd ? api.addToOrders.bind(api) : api.removeFromOrders.bind(api)
    method({ id }).then(res => {
      const recipesUpdated = recipes.map(recipe => {
        if (recipe.id === id) {
          recipe.is_in_shopping_cart = toAdd
        }
        return recipe
      })
      setRecipes(recipesUpdated)
      callback && callback(toAdd)
    })
    .catch(err => {
      const { errors } = err
      if (errors) {
        alert(errors)
      }
    })
  }

  return {
    recipes,
    setRecipes,
    recipesCount,
    setRecipesCount,
    recipesPage,
    setRecipesPage,
    tagsValue,
    handleLike,
    handleAddToCart,
    handleTagsChange: handleTagsChangeWithUrl,
    setTagsValue
  }
}